from manim import *

class PhysicsExample(Scene):
    def construct(self):
        # 1. Projectile Motion
        ground = Line(LEFT * 5, RIGHT * 5, color=DARK_GREY).shift(DOWN * 2)
        ball = Dot(color=YELLOW).move_to(LEFT * 4 + DOWN * 2)
        
        self.play(Create(ground))
        self.play(FadeIn(ball))
        
        # Parabolic path
        curve = ArcBetweenPoints(LEFT * 4 + DOWN * 2, RIGHT * 4 + DOWN * 2, angle=-TAU/4, color=WHITE)
        self.play(MoveAlongPath(ball, curve), run_time=3)
        self.wait(1)

        # 2. Pendulum
        pivot = Dot(point=[0, 3, 0], color=WHITE)
        bob = Dot(point=[2, 0, 0], color=RED)
        string = Line(pivot.get_center(), bob.get_center(), stroke_width=2)
        
        self.play(Create(pivot), Create(string), Create(bob))
        
        # Swing back and forth
        for _ in range(2):
            self.play(
                Rotate(string, angle=-PI/2, about_point=pivot.get_center()),
                bob.animate.move_to(pivot.get_center() + 3 * DOWN + 2 * LEFT),
                run_time=2, rate_func=slow_into
            )
            self.play(
                Rotate(string, angle=PI/2, about_point=pivot.get_center()),
                bob.animate.move_to(pivot.get_center() + 3 * DOWN + 2 * RIGHT),
                run_time=2, rate_func=slow_into
            )
        
        self.wait(2)
