from manim import *

class WhiteboardExample(Scene):
    def construct(self):
        # 1. Sketchy Rectangle (Box)
        # Using multiple slightly offset lines for hand-drawn feel
        box = Rectangle(height=3, width=5, color=WHITE).shift(UP * 2)
        
        # Sketchy box border
        lines = VGroup(*[
            Line(UP * 3.5 + LEFT * 2.5, UP * 3.5 + RIGHT * 2.5, stroke_width=2),
            Line(UP * 0.5 + LEFT * 2.5, UP * 0.5 + RIGHT * 2.5, stroke_width=2.5),
            Line(UP * 3.5 + LEFT * 2.5, UP * 0.5 + LEFT * 2.5, stroke_width=3),
            Line(UP * 3.5 + RIGHT * 2.5, UP * 0.5 + RIGHT * 2.5, stroke_width=2.5)
        ])
        
        self.play(Create(lines), run_time=2)
        self.wait(1)

        # 2. Text in box
        msg = Text("Write here!", font_size=32).move_to(lines.get_center())
        self.play(Write(msg), run_time=2)
        self.wait(2)

        # 3. Sketchy Arrow
        arrow_body = Line(DOWN * 2 + LEFT * 1, DOWN * 2 + RIGHT * 1, stroke_width=4, color=YELLOW)
        arrow_head = VGroup(*[
            Line(DOWN * 2 + RIGHT * 1, DOWN * 1.5 + RIGHT * 0.5, stroke_width=4, color=YELLOW),
            Line(DOWN * 2 + RIGHT * 1, DOWN * 2.5 + RIGHT * 0.5, stroke_width=4, color=YELLOW)
        ])
        
        self.play(Create(arrow_body), Create(arrow_head), run_time=2)
        self.wait(1)

        # 4. Rough Circle (sketchy)
        rough_circle = VGroup(*[
            Arc(radius=1.5, start_angle=0, angle=PI, color=WHITE),
            Arc(radius=1.6, start_angle=PI, angle=PI+0.1, color=WHITE)
        ]).shift(DOWN * 2 + LEFT * 3)
        
        self.play(Create(rough_circle), run_time=2)
        self.wait(3)
        
        # Total ≈ 15s
        self.play(FadeOut(Group(*self.mobjects)), run_time=2)
