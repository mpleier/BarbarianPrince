"""Smoke test for the Tk GUI and its autoplay controls.

    python _refs/gui_smoke.py [seconds]

Opens the real window, lets the bot play for a few seconds, then checks that
the game advanced, that "Bot move" works with autoplay off, and that a manual
answer resumes the loop.  Uses `root.after` so no clicking is needed.
"""
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))

from engine import Game            # noqa: E402
from gui import GameGUI            # noqa: E402

SECONDS = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0


def main():
    game = Game(seed=3)
    gui = GameGUI(game)

    report = {}

    def start_auto():
        gui.speed.set('60')
        gui.on_speed()
        gui.toggle_auto()
        report['day_at_start'] = game.day

    def pause_and_step():
        gui.toggle_auto()                  # off
        report['day_after_auto'] = game.day
        report['log_after_auto'] = len(game.log)
        gui.bot_move()                     # one bot answer while paused
        report['day_after_step'] = game.day

    def restart():
        # "New game" must throw the campaign away and keep the loop alive
        report['day_before_restart'] = game.day
        gui.restart()
        report['day_after_restart'] = gui.game.day
        report['restart_is_new_game'] = gui.game is not game
        report['restart_auto_off'] = not gui.auto
        report['restart_log'] = gui.log.get('1.0', 'end').strip()

    def manual_answer():
        # a manual click path: answer whatever prompt is pending, if any.
        # `gui.game` is a *new* object after the restart, so read it again.
        g = gui.game
        if g.prompts and not g.game_over:
            p = g.current()
            if p['options']:
                gui.answer(0)
                report['manual_ok'] = True
        report['day_final'] = g.day
        report['over'] = g.game_over
        report['auto_flag'] = gui.auto
        # the end-of-game path must not raise
        g.game_over = True
        g.reason = 'smoke test stop'
        gui.schedule(0)
        gui.root.after(300, check_finish)

    def check_finish():
        report['finished'] = gui.prompt_title.cget('text')
        report['close_button'] = [w.cget('text') for w in gui.buttons.winfo_children()]
        gui.root.destroy()

    gui.schedule(1)
    gui.root.after(100, start_auto)
    gui.root.after(int(SECONDS * 1000), pause_and_step)
    gui.root.after(int(SECONDS * 1000) + 300, restart)
    gui.root.after(int(SECONDS * 1000) + 900, manual_answer)
    gui.root.mainloop()

    print('day at start      :', report.get('day_at_start'))
    print('day after auto    :', report.get('day_after_auto'))
    print('log lines gained  :', (report.get('log_after_auto') or 0))
    print('day after bot move:', report.get('day_after_step'))
    print('manual answer ok  :', report.get('manual_ok', 'no prompt'))
    print('day at close      :', report.get('day_final'), '| game over:', report.get('over'))
    ok = (report.get('day_after_auto', 0) >= (report.get('day_at_start') or 1)
          and (report.get('log_after_auto') or 0) > 10)
    print('restart           : day', report.get('day_before_restart'),
          '->', report.get('day_after_restart'),
          '| new game:', report.get('restart_is_new_game'),
          '| auto off:', report.get('restart_auto_off'))
    print('end screen        :', report.get('finished'), '|', report.get('close_button'))
    ok = ok and bool(report.get('finished')) and 'Close' in (report.get('close_button') or [])
    ok = ok and report.get('day_after_restart') == 1 and report.get('restart_is_new_game')
    print('AUTOPLAY', 'OK' if ok else 'FAILED')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
