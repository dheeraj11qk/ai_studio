from manim import *

class UIUXExample(Scene):
    def construct(self):
        # 1. SMARTPHONE FRAME
        frame = RoundedRectangle(corner_radius=0.4, height=6.5, width=3.2, color=GRAY)
        screen = RoundedRectangle(corner_radius=0.2, height=6, width=2.8, color=BLACK).move_to(frame.get_center())
        
        self.play(Create(frame), FadeIn(screen))
        
        # 2. STATUS BAR
        status_bar = Rectangle(height=0.25, width=2.8, color=DARK_GREY).shift(UP * 2.8)
        self.play(FadeIn(status_bar))
        
        # 3. LIST OF ITEMS (CARDS)
        cards = VGroup(*[
            RoundedRectangle(corner_radius=0.1, height=1.2, width=2.5, color=GREY_B).shift(UP * (1.5 - (i * 1.5)))
            for i in range(3)
        ])
        
        card_labels = VGroup(*[
            Text(f"Message {i+1}", font_size=18).move_to(cards[i].get_center())
            for i in range(3)
        ])
        
        self.play(Create(cards), Write(card_labels), run_time=3)
        
        # 4. BUTTON CLICK ACTION
        button = Circle(radius=0.3, color=BLUE).shift(DOWN * 2.5)
        plus = Text("+", color=WHITE).move_to(button.get_center())
        
        self.play(Create(button), Write(plus))
        
        # Simulate a click (scale up and down)
        self.play(button.animate.scale(1.2), plus.animate.scale(1.2), run_time=0.2)
        self.play(button.animate.scale(1/1.2), plus.animate.scale(1/1.2), run_time=0.2)
        
        # New card appears
        new_card = RoundedRectangle(corner_radius=0.1, height=1.2, width=2.5, color=GREEN).move_to(cards[0])
        self.play(FadeIn(new_card), run_time=1)
        self.wait(3)
