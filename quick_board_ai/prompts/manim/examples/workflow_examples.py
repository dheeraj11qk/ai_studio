from manim import *

class WorkflowExample(Scene):
    def construct(self):
        # 1. Start Node (Circle)
        start = Circle(radius=0.7, color=GREEN).shift(UP * 3)
        start_label = Text("Start").scale(0.6).move_to(start.get_center())
        
        self.play(Create(start), Write(start_label))
        self.wait(1)

        # 2. Process Node (Rectangle)
        process = Rectangle(height=1.2, width=3, color=BLUE).shift(UP * 1)
        process_label = Text("Save Data").scale(0.6).move_to(process.get_center())
        
        arrow1 = Arrow(start.get_bottom(), process.get_top(), color=WHITE)
        self.play(Create(arrow1), Create(process), Write(process_label))
        self.wait(1)

        # 3. Decision Node (Diamond based on Square)
        decision = Square(side_length=1.5, color=YELLOW).rotate(PI/4).shift(DOWN * 1.5)
        decision_label = Text("Success?").scale(0.5).move_to(decision.get_center()).rotate(-PI/4)
        
        arrow2 = Arrow(process.get_bottom(), decision.get_top(), color=WHITE)
        self.play(Create(arrow2), Create(decision), Write(decision_label))
        self.wait(1)

        # 4. Branches (True/False)
        # Success (Right branch)
        end = Circle(radius=0.7, color=MAROON).shift(DOWN * 3.5 + RIGHT * 3)
        end_label = Text("Done").scale(0.6).move_to(end.get_center())
        
        arrow_yes = Arrow(decision.get_right(), end.get_top(), color=WHITE)
        label_yes = Text("Yes", color=GREEN).scale(0.4).next_to(arrow_yes, RIGHT)
        
        # Failure (Left branch)
        fail = Square(side_length=1, color=RED).shift(DOWN * 3.5 + LEFT * 3)
        fail_label = Text("Error").scale(0.6).move_to(fail.get_center())
        
        arrow_no = Arrow(decision.get_left(), fail.get_top(), color=WHITE)
        label_no = Text("No", color=RED).scale(0.4).next_to(arrow_no, LEFT)
        
        self.play(Create(arrow_yes), Write(label_yes), Create(end), Write(end_label))
        self.play(Create(arrow_no), Write(label_no), Create(fail), Write(fail_label))

        self.wait(3)
