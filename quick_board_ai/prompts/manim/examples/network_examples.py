from manim import *

class NetworkExample(Scene):
    def construct(self):
        # 1. NODES (WHITEBOARD STYLE)
        # Creating a central node and connections
        central_node = Circle(radius=1.0, color=BLUE).shift(UP * 1)
        center_text = Text("Cloud").scale(0.8).move_to(central_node.get_center())
        
        self.play(Create(central_node), Write(center_text))
        self.wait(1)

        # 2. DEVICE NODES
        devices = VGroup(
            Circle(radius=0.5, color=WHITE).shift(DOWN * 2 + LEFT * 3),
            Circle(radius=0.5, color=WHITE).shift(DOWN * 2 + RIGHT * 3),
            Circle(radius=0.5, color=WHITE).shift(DOWN * 2)
        )
        
        device_labels = VGroup(
            Text("Phone").next_to(devices[0], DOWN).scale(0.5),
            Text("Laptop").next_to(devices[1], DOWN).scale(0.5),
            Text("Tablet").next_to(devices[2], DOWN).scale(0.5)
        )
        
        self.play(Create(devices), Write(device_labels), run_time=2)

        # 3. CONNECTIONS (EDGES)
        connections = VGroup(*[
            Line(central_node.get_center(), dev.get_center(), color=GRAY, stroke_width=2)
            for dev in devices
        ])
        
        self.play(Create(connections), run_time=2)
        self.wait(1)

        # 4. SEND DATA PULSE (DOT MOVING ALONG LINE)
        pulse = Dot(color=YELLOW).move_to(central_node.get_center())
        self.play(FadeIn(pulse))
        
        # Animate pulse to each device
        for dev in devices:
            self.play(pulse.animate.move_to(dev.get_center()), run_time=1)
            self.play(pulse.animate.move_to(central_node.get_center()), run_time=0.5)

        self.play(FadeOut(pulse))
        self.wait(2)
