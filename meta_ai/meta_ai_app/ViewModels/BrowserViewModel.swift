


import SwiftUI
import WebKit
import Combine
import Swifter

class BrowserViewModel: NSObject, ObservableObject, WKNavigationDelegate, WKScriptMessageHandler {

    @Published var webView = WKWebView()
    @Published var progress: Double = 0
    @Published var downloads: [DownloadItem] = []
    @Published var showDownloads = false
    @Published var isDownloading = false
    let server = HttpServer()
    var videoReady = false
    var videoPath = ""
    var lastPrompt = ""
    var isWaitingForDownload = false
    var waitingForClear = false
    var knownVideoCount = 0  // track how many videos were on page before new prompt


    override init() {

        let config = WKWebViewConfiguration()
        config.websiteDataStore = WKWebsiteDataStore.default()

        // JavaScript listener for blob downloads
        let script = """
        document.addEventListener('click', function(e){

            const a = e.target.closest('a');
            if(!a) return;

            const href = a.href || "";

            if(href.startsWith("blob:")){

                fetch(href)
                .then(r => r.blob())
                .then(blob => {

                    const reader = new FileReader();

                    reader.onloadend = function(){
                        window.webkit.messageHandlers.download.postMessage(reader.result);
                    };

                    reader.readAsDataURL(blob);

                });

                e.preventDefault();
                return;
            }

        });
        """

        let contentController = WKUserContentController()

        contentController.addUserScript(
            WKUserScript(
                source: script,
                injectionTime: .atDocumentEnd,
                forMainFrameOnly: false
            )
        )

        config.userContentController = contentController

        webView = WKWebView(frame: .zero, configuration: config)

        super.init()

        startServer()
        watchVideoReady()

        // Auto-load meta.ai on launch
        load(urlString: "https://www.meta.ai/")

        contentController.add(self, name: "download")

        webView.navigationDelegate = self

        webView.addObserver(
            self,
            forKeyPath: "estimatedProgress",
            options: .new,
            context: nil
        )
    }

    // MARK: Progress

    override func observeValue(
        forKeyPath keyPath: String?,
        of object: Any?,
        change: [NSKeyValueChangeKey : Any]?,
        context: UnsafeMutableRawPointer?
    ) {

        if keyPath == "estimatedProgress" {
            progress = webView.estimatedProgress
        }
    }

    // MARK: Navigation

    func load(urlString: String) {

        var text = urlString

        if !text.contains("http") {
            text = "https://www.google.com/search?q=\(text)"
        }

        if let url = URL(string: text) {
            webView.load(URLRequest(url: url))
        }
    }

    func goBack() {
        if webView.canGoBack { webView.goBack() }
    }

    func goForward() {
        if webView.canGoForward { webView.goForward() }
    }

    func reload() {
        webView.reload()
    }

    // MARK: Navigation policy

    func webView(_ webView: WKWebView,
                 decidePolicyFor navigationAction: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {

        decisionHandler(.allow)
    }

    // MARK: JS message handler

    func userContentController(
        _ userContentController: WKUserContentController,
        didReceive message: WKScriptMessage
    ) {

        guard message.name == "download" else { return }

        // blob base64 download
        if let base64 = message.body as? String,
           base64.starts(with: "data:") {

            saveBase64File(base64)
        }
    }

    // MARK: Save blob file — saves inside app sandbox Documents folder

    func saveBase64File(_ base64: String) {

        guard let comma = base64.firstIndex(of: ",") else { return }

        let meta = base64[..<comma]
        let dataString = base64[base64.index(after: comma)...]

        guard let data = Data(base64Encoded: String(dataString)) else { return }

        var ext = "file"

        if meta.contains("video/mp4") { ext = "mp4" }
        if meta.contains("image/png") { ext = "png" }
        if meta.contains("image/jpeg") { ext = "jpg" }
        if meta.contains("image/webp") { ext = "webp" }

        let filename = "download_\(UUID().uuidString).\(ext)"

        // Save inside app sandbox Documents — always writable
        let docsFolder = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first!
        let fileURL = docsFolder.appendingPathComponent(filename)

        do {
            try data.write(to: fileURL)

            DispatchQueue.main.async {
                self.downloads.append(
                    DownloadItem(filename: filename, progress: 1, status: "Completed")
                )
                self.isDownloading = false
                self.videoPath = fileURL.path
                self.videoReady = true
                print("Video saved in sandbox at:", fileURL.path)
            }

        } catch {
            print("Save failed:", error)
        }
    }
    
    
    func startServer() {
        
        
        
        
        server.POST["/generate"] = { request in

            // Convert body bytes to Data
            let data = Data(request.body)

            // Parse JSON
            guard let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                  let prompt = json["prompt"] as? String else {

                return HttpResponse.ok(.json(["status": "error"]))
            }

            DispatchQueue.main.async {

                // Reset state for new generation
                self.videoReady = false
                self.videoPath = ""
                self.lastPrompt = prompt
                self.isWaitingForDownload = false
                self.waitingForClear = false

                // Snapshot current video count so we detect the NEW one
                let countJS = "document.querySelectorAll('[data-testid=\"generated-video\"]').length"
                self.webView.evaluateJavaScript(countJS) { result, _ in
                    self.knownVideoCount = result as? Int ?? 0
                    print("[Generate] Current video count:", self.knownVideoCount)
                }

                let js = """
                var textarea = document.querySelector('textarea');
                if(textarea){
                    textarea.value = "\(prompt)";
                    textarea.dispatchEvent(new Event('input',{bubbles:true}));
                }
                """

                self.webView.evaluateJavaScript(js)

                // delay 2 seconds then click send
                DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {

                    let clickJS = """
                    var sendBtn = document.querySelector('[data-testid="composer-send-button"]');
                    if(sendBtn){ sendBtn.click(); }
                    """

                    self.webView.evaluateJavaScript(clickJS)
                }
            }

            return HttpResponse.ok(.json([
                "status": "sent",
                "prompt": prompt
            ]))
        }
        
        server["/status"] = { request in

            guard self.videoReady, !self.videoPath.isEmpty else {
                return HttpResponse.ok(.json(["status": "processing"]))
            }

            // Read the video file and return as base64 so Python can save it outside sandbox
            guard let data = FileManager.default.contents(atPath: self.videoPath) else {
                return HttpResponse.ok(.json(["status": "error", "message": "file not readable"]))
            }

            let base64 = data.base64EncodedString()
            let filename = URL(fileURLWithPath: self.videoPath).lastPathComponent

            return HttpResponse.ok(.json([
                "status": "completed",
                "filename": filename,
                "data": base64
            ]))
        }

        // Delete the video file from inside the app sandbox after Python has saved it
        server.POST["/delete"] = { request in
            let pathToDelete = self.videoPath
            guard !pathToDelete.isEmpty else {
                return HttpResponse.ok(.json(["status": "nothing_to_delete"]))
            }
            do {
                try FileManager.default.removeItem(atPath: pathToDelete)
                DispatchQueue.main.async {
                    self.videoPath = ""
                    self.videoReady = false
                }
                print("Deleted sandbox file:", pathToDelete)
                return HttpResponse.ok(.json(["status": "deleted", "file": pathToDelete]))
            } catch {
                print("Delete failed:", error)
                return HttpResponse.ok(.json(["status": "error", "message": error.localizedDescription]))
            }
        }

        // Debug endpoint — returns all data-testid values on the page
        server["/debug"] = { request in
            var result = ""
            let sema = DispatchSemaphore(value: 0)

            DispatchQueue.main.async {
                let js = """
                (function(){
                    let els = document.querySelectorAll('[data-testid]');
                    let ids = Array.from(els).map(e => e.getAttribute('data-testid'));
                    return ids.join(',');
                })();
                """
                self.webView.evaluateJavaScript(js) { res, _ in
                    result = res as? String ?? "none"
                    sema.signal()
                }
            }
            sema.wait()
            return HttpResponse.ok(.json(["testids": result]))
        }


        do {
            try server.start(5003)
            print("✅ Server started successfully at http://localhost:5003")
        } catch {
            print("❌ Server failed to start on port 5003: \(error)")
            print("Trying alternative port 5004...")
            do {
                try server.start(5004)
                print("✅ Server started on alternative port 5004")
            } catch {
                print("❌ Server failed on port 5004 too: \(error)")
            }
        }
    }
    
    
    func watchVideoReady(){

        Timer.scheduledTimer(withTimeInterval: 2, repeats: true){ _ in

            guard !self.lastPrompt.isEmpty,
                  !self.videoReady,
                  !self.isWaitingForDownload else { return }

            let js = """
            (function(){
                let videos = document.querySelectorAll('[data-testid="generated-video"]');
                return videos.length;
            })();
            """

            self.webView.evaluateJavaScript(js){ result, _ in

                let count = result as? Int ?? 0
                print("[Timer] videoCount=\(count) knownCount=\(self.knownVideoCount)")

                if count > self.knownVideoCount {
                    self.isWaitingForDownload = true
                    print("[Timer] New video detected — waiting 5s then downloading")
                    DispatchQueue.main.asyncAfter(deadline: .now() + 5.0) {
                        // click the LAST download button (newest video)
                        self.clickDownload()
                    }
                }
            }
        }
    }

    func clickDownload(){

        let js = """
        (function(){
            let buttons = document.querySelectorAll('button[aria-label="Download"]');
            if(buttons.length > 0){
                buttons[buttons.length - 1].click();
                return "download_clicked:" + buttons.length;
            }
            return "no_button";
        })();
        """

        webView.evaluateJavaScript(js){ result, error in
            print("Download click result:", result ?? "nil")
        }
    }
    
}
