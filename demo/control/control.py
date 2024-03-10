from operator import not_

from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from debatrix.platform import Platform

from ..base import BaseUI


class ControlUI(BaseUI[Platform, ui.dialog, ui.dialog]):
    def init_ui(self, platform: Platform, dlg_config: ui.dialog, dlg_detail: ui.dialog) -> None:
        async def hdl_sel_debate(e: ValueChangeEventArguments) -> None:
            await platform.select_debate(e.value)

        async def hdl_btn_config() -> None:
            with platform._bg_task():
                await dlg_config
            if await platform.update_config():
                ui.notify("Config saved", type="info")

        async def hdl_btn_detail() -> None:
            await dlg_detail

        async def hdl_btn_reset() -> None:
            await platform.reset_debate()

        async def hdl_btn_start() -> None:
            await platform.reset_debate()
            await platform.start_debate()

        async def hdl_btn_stop() -> None:
            await platform.stop_debate()

        async def hdl_btn_save() -> None:
            await platform.save_record()

        with ui.grid(columns=6).classes("w-full"):
            ui.select(
                {
                    motion_id: f'<span class="line-clamp-1">{motion}</span>'
                    for motion_id, motion in platform.motions
                },
                label="Motion",
                on_change=hdl_sel_debate,
                clearable=True,
            ).props('options-html behavior="dialog"').classes("col-span-6").bind_enabled_from(
                platform, target_name="is_config_enabled"
            )

            ui.button("Config", on_click=hdl_btn_config, icon="settings").classes(
                "col-span-3"
            ).bind_enabled_from(platform, target_name="is_config_enabled")

            ui.button("Detail", on_click=hdl_btn_detail, icon="open_in_new").classes(
                "col-span-3"
            ).bind_enabled_from(platform, target_name="is_debate_loaded")

            ui.button("Reset", on_click=hdl_btn_reset, icon="restart_alt").classes(
                "col-span-3 sm:col-span-2 xl:col-span-3 2xl:col-span-2"
            ).bind_enabled_from(platform, target_name="is_control_enabled")

            ui.button("Save", on_click=hdl_btn_save, icon="save").classes(
                "col-span-3 sm:col-span-2 xl:col-span-3 2xl:col-span-2"
            ).bind_enabled_from(platform, target_name="is_control_enabled")

            ui.button(
                "Start", on_click=hdl_btn_start, color="positive", icon="play_circle"
            ).classes("col-span-6 sm:col-span-2 xl:col-span-6 2xl:col-span-2").bind_enabled_from(
                platform, target_name="is_control_enabled"
            ).bind_visibility_from(
                platform, target_name="is_start_stop_toggled", backward=not_
            )

            ui.button("Stop", on_click=hdl_btn_stop, color="negative", icon="stop_circled").classes(
                "col-span-6 2xl:col-span-2"
            ).bind_visibility_from(platform, target_name="is_start_stop_toggled")
