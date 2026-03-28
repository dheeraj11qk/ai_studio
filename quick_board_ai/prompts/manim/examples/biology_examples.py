from manim import *

class BiologyExample(Scene):
    def construct(self):
        # 1. ANIMAL CELL
        cell = Circle(radius=2, color=BLUE_B).shift(LEFT * 2.5)
        nucleus = Circle(radius=0.5, color=PURPLE_B).move_to(cell.get_center())
        organelle1 = Dot(color=YELLOW).shift(LEFT * 2.5 + UP * 1)
        organelle2 = Dot(color=PINK).shift(LEFT * 2.5 + DOWN * 0.5)
        
        self.play(Create(cell), run_time=2)
        self.play(Create(nucleus), FadeIn(organelle1, organelle2))
        
        label = Text("Animal Cell", font_size=24).next_to(cell, DOWN)
        self.play(Write(label))
        self.wait(1)

        # 2. DNA HELIX (WHITEBOARD STYLE)
        dna_group = VGroup()
        for i in range(10):
            # Left side wave
            left_dot = Dot(point=[2, (i * 0.5) - 2, 0], color=GREEN)
            # Right side wave
            right_dot = Dot(point=[4, (i * 0.5) - 2.5, 0], color=GREEN)
            
            # Connection
            connector = Line(left_dot.get_center(), right_dot.get_center(), stroke_width=2, color=WHITE)
            dna_group.add(left_dot, right_dot, connector)
            
        self.play(Create(dna_group), run_time=3)
        
        dna_label = Text("DNA Structure", font_size=24).next_to(dna_group, DOWN)
        self.play(Write(dna_label))
        self.wait(2)
