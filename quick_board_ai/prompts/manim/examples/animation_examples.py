from manim import *

class AnimationExample(Scene):
    def construct(self):
        # 1. Transform: Morphing shapes
        circle = Circle(color=WHITE).shift(LEFT * 3)
        square = Square(color=BLUE).shift(RIGHT * 3)
        
        self.play(Create(circle), run_time=2)
        self.wait(1)
        self.play(Transform(circle, square), run_time=2)
        self.wait(2)

        # 2. Moving along path (Curve)
        dot = Dot(color=YELLOW).move_to(circle.get_center())
        path = Line(LEFT * 3, RIGHT * 3 + UP * 2, color=GRAY)
        self.play(Create(path), run_time=1)
        self.play(MoveAlongPath(dot, path), run_time=3)
        self.wait(1)

        # 3. Mass FadeOut
        all_objects = VGroup(*[circle, square, dot, path])
        self.play(FadeOut(all_objects), run_time=2)
        
        # 4. Text and GrowFromCenter
        final_msg = Text("The End", color=GREEN).scale(1.5)
        self.play(GrowFromCenter(final_msg), run_time=2)
        self.wait(3)
