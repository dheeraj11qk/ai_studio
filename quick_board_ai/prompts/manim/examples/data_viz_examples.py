from manim import *

class DataVizExample(Scene):
    def construct(self):
        # 1. BAR CHART CONCEPT
        title = Text("Sales Data", font_size=32).to_edge(UP)
        self.play(Write(title))
        self.wait(1)

        # Draw axis (Whiteboard Style)
        x_axis = Line(LEFT * 4, RIGHT * 4, color=WHITE).shift(DOWN * 2)
        y_axis = Line(DOWN * 2, UP * 2, color=WHITE).shift(LEFT * 4)
        self.play(Create(x_axis), Create(y_axis))

        # Bars
        data = [2, 3.5, 1.5, 4]
        colors = [BLUE, GREEN, YELLOW, MAROON]
        bars = VGroup()
        for i, val in enumerate(data):
            bar = Rectangle(height=val, width=1.2, color=colors[i], fill_opacity=0.5).shift(DOWN * (2 - val/2) + LEFT * (2.4 - (i * 2)))
            bars.add(bar)
        
        self.play(Create(bars), run_time=3)
        self.wait(2)

        # 2. PIE CHART CONCEPT (ARCS)
        slices = VGroup(
            Arc(radius=1.8, start_angle=0, angle=TAU * 0.4, color=RED, stroke_width=40), # 40%
            Arc(radius=1.8, start_angle=TAU * 0.4, angle=TAU * 0.3, color=BLUE, stroke_width=40), # 30%
            Arc(radius=1.8, start_angle=TAU * 0.7, angle=TAU * 0.3, color=GREEN, stroke_width=40) # 30%
        ).shift(RIGHT * 3 + UP * 1)
        
        self.play(Create(slices), run_time=3)
        self.wait(3)
        
        # 3. LEGEND
        legend = VGroup(
            Text("Product A - 40%", font_size=20, color=RED).shift(RIGHT * 4 + DOWN * 1.5),
            Text("Product B - 30%", font_size=20, color=BLUE).shift(RIGHT * 4 + DOWN * 2),
            Text("Product C - 30%", font_size=20, color=GREEN).shift(RIGHT * 4 + DOWN * 2.5)
        )
        self.play(Write(legend))
        self.wait(3)
