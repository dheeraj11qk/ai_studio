from manim import *

class MathExample(Scene):
    def construct(self):
        # Title
        title = Text("Mathematics Visualization").to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # Draw a Cartesian bridge
        x_axis = Line(LEFT * 3, RIGHT * 3, color=WHITE)
        y_axis = Line(DOWN * 2, UP * 2, color=WHITE)
        self.play(Create(x_axis), Create(y_axis))

        # Quadratic Curve points (Whiteboard Style)
        points = [
            Dot(point=[x, 0.5 * (x**2), 0], color=YELLOW)
            for x in range(-2, 3)
        ]
        curve_lines = VGroup(*[
            Line(points[i].get_center(), points[i+1].get_center(), color=YELLOW)
            for i in range(len(points)-1)
        ])
        
        self.play(Create(VGroup(*points)), run_time=2)
        self.play(Create(curve_lines))
        self.wait(2)

        # Simple Arithmetic Text
        eq = Text("2 + 2 = 4", font_size=36).shift(DOWN * 3)
        self.play(Write(eq))
        self.wait(2)
