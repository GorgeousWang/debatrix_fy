import re
from asyncio import TaskGroup
from collections.abc import Iterable, Mapping
from typing import Any

from nicegui import ui

from debatrix.core.action import AllPanelActions, JudgeAction, PanelAction
from debatrix.core.common import DebaterName, DimensionName, Speech, Verdict

from ..base import BaseUI
from .score import ScoreUI
from .winner import WinnerUI


class VerdictUI(BaseUI[Iterable[DimensionName] | None, Mapping[DebaterName, str] | None]):
    def init_ui(
        self,
        dimensions_name: Iterable[DimensionName] | None,
        debaters_bg_color: Mapping[DebaterName, str] | None,
    ) -> None:
        debaters: Iterable[DebaterName] | None = (
            None if debaters_bg_color is None else debaters_bg_color.keys()
        )

        with ui.tabs().props("dense").classes("w-full mb-0") as verdict_tabs:
            ui.tab("winner", label="Winner", icon="emoji_events")
            ui.tab("score", label="Score", icon="scoreboard")

        with ui.tab_panels(verdict_tabs, value="winner").classes("w-full grow"):
            with ui.tab_panel("winner"):
                self._ui_winner = WinnerUI()
                self._ui_winner.register_ui(dimensions_name, debaters)

            with ui.tab_panel("score").classes("px-0"):
                self._ui_score = ScoreUI()
                self._ui_score.register_ui(dimensions_name, debaters_bg_color)

    async def init_chat(self) -> None:
        async with TaskGroup() as tg:
            tg.create_task(self._ui_winner.init_chat())
            tg.create_task(self._ui_score.init_chat())

    async def pre_panel_action_callback(
        self, *args: Any, action: AllPanelActions, dimension_name: DimensionName
    ) -> None:
        async with TaskGroup() as tg:
            if action == JudgeAction.UPDATE:
                speech: Speech = args[0]

                tg.create_task(
                    self._ui_winner.start_analysis(
                        dimension_name=dimension_name, speech_index=speech.index
                    )
                )

                tg.create_task(
                    self._ui_score.start_analysis(
                        dimension_name=dimension_name,
                        debater_name=speech.debater_name,
                        speech_index=speech.index,
                    )
                )
            elif action in (JudgeAction.JUDGE, PanelAction.SUMMARIZE):
                tg.create_task(self._ui_winner.start_verdict(dimension_name=dimension_name))
                tg.create_task(self._ui_score.start_verdict(dimension_name=dimension_name))

    async def in_panel_action_callback(
        self, chat_chunk: tuple[str, str], *, action: AllPanelActions, dimension_name: DimensionName
    ) -> None:
        match: re.Match | None = re.fullmatch(r"# Temporary Score of ([^:]+): (.+)", chat_chunk[1])

        if action == JudgeAction.UPDATE and chat_chunk[0] == "extra" and match is not None:
            self._ui_score.update_analysis(
                dimension_name=dimension_name,
                debater_name=DebaterName(match.group(1)),
                score=eval(match.group(2)),
            )

    async def post_panel_action_callback(
        self, *args: Any, action: AllPanelActions, dimension_name: DimensionName
    ) -> None:
        async with TaskGroup() as tg:
            if action in (JudgeAction.JUDGE, PanelAction.SUMMARIZE):
                verdict: Verdict = args[0]

                tg.create_task(
                    self._ui_winner.update_verdict(dimension_name=dimension_name, verdict=verdict)
                )

                tg.create_task(
                    self._ui_score.update_verdict(dimension_name=dimension_name, verdict=verdict)
                )

    async def start_judge(self) -> None:
        async with TaskGroup() as tg:
            tg.create_task(self._ui_winner.start_judge())
            tg.create_task(self._ui_score.start_judge())
