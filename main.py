import threading
import flet as ft
from flet import icons, colors

import core


def main(page: ft.Page):
    page.title = core.APP_NAME
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 14
    page.scroll = ft.ScrollMode.AUTO

    cfg = dict(core.DEFAULT_CFG)

    title = ft.Text(core.APP_NAME, size=24, weight=ft.FontWeight.BOLD, color=colors.BLUE_800)
    subtitle = ft.Text('大盘环境 + 资金面 + 板块轮动 + 个股硬条件 四维选股', size=12, color=colors.GREY_600)

    market_label = ft.Text('大盘环境：加载中...', size=15, weight=ft.FontWeight.W_600)
    industry_label = ft.Text('', size=12, color=colors.GREY_700)

    scan_btn = ft.ElevatedButton('开始扫描', icon=icons.PLAY_ARROW, bgcolor=colors.BLUE_700, color=colors.WHITE)
    progress = ft.ProgressBar(width=600, visible=False)
    progress_text = ft.Text('', size=12, color=colors.GREY_700)

    cfg_btn = ft.TextButton('筛选参数', icon=icons.TUNE)

    top_n_field = ft.TextField(label='展示数量', value=str(cfg['top_n']), width=100, text_align=ft.TextAlign.CENTER)
    min_flow_field = ft.TextField(label='主力净流入(万)', value=str(cfg['min_flow']), width=130, text_align=ft.TextAlign.CENTER)
    max_price_field = ft.TextField(label='最高价', value=str(cfg['max_price']), width=90, text_align=ft.TextAlign.CENTER)
    min_chg_field = ft.TextField(label='最低涨幅%', value=str(cfg['min_chg']), width=100, text_align=ft.TextAlign.CENTER)
    ck_kcb = ft.Checkbox(label='排除科创板', value=cfg['exclude_kcb'])
    ck_bj = ft.Checkbox(label='排除北交所', value=cfg['exclude_bj'])

    cfg_panel = ft.Container(
        visible=False,
        padding=10,
        bgcolor=colors.GREY_100,
        border_radius=8,
        content=ft.Column([
            ft.Row([max_price_field, min_chg_field, top_n_field], wrap=True),
            ft.Row([min_flow_field, ck_kcb, ck_bj], wrap=True),
        ]),
    )

    def toggle_cfg(e):
        cfg_panel.visible = not cfg_panel.visible
        page.update()

    cfg_btn.on_click = toggle_cfg

    result_count = ft.Text('等待扫描...', size=13, color=colors.GREY_700)
    result_list = ft.ListView(expand=True, height=520, spacing=4, padding=4)

    def read_cfg():
        try:
            cfg['top_n'] = int(top_n_field.value or 30)
            cfg['min_flow'] = float(min_flow_field.value or 0)
            cfg['max_price'] = float(max_price_field.value or 35)
            cfg['min_chg'] = float(min_chg_field.value or 3)
            cfg['exclude_kcb'] = bool(ck_kcb.value)
            cfg['exclude_bj'] = bool(ck_bj.value)
            return True
        except ValueError:
            result_count.value = '参数错误：请填写有效数字'
            page.update()
            return False

    def do_scan():
        if not read_cfg():
            return
        progress.visible = True
        progress.value = 0
        progress_text.value = '正在拉取全市场数据(约5500只)...'
        scan_btn.disabled = True
        result_count.value = '扫描中...'
        result_list.controls.clear()
        page.update()
        try:
            def on_progress(done, total):
                progress.value = (done / total) if total else 0
                progress_text.value = '%d / %d' % (done, total)
                page.update()

            stocks = core.get_market_snapshot(on_progress)
            results = core.filter_stocks(stocks, cfg)

            try:
                idx = core.get_index_snapshot()
                env, advice = core.judge_market(idx)
                market_label.value = '大盘环境：%s ｜ %s' % (env, advice)
                sh = idx.get('上证指数')
                if sh and sh.get('change_pct') is not None:
                    pct = sh['change_pct']
                    market_label.color = colors.RED_700 if pct > 0 else (colors.GREEN_700 if pct < 0 else colors.GREY_700)
            except Exception:
                market_label.value = '大盘环境：获取失败，可稍后重试'

            try:
                ind = core.get_industry_rank()[:6]
                industry_label.value = '领涨板块: ' + '  |  '.join(
                    '%s %+.2f%%' % (s.get('f14', ''), float(s.get('f3') or 0)) for s in ind)
            except Exception:
                industry_label.value = ''

            n = min(cfg['top_n'], len(results))
            for i, s in enumerate(results[:cfg['top_n']]):
                chg = s['change_pct']
                chg_color = colors.RED_700 if chg > 0 else (colors.GREEN_700 if chg < 0 else colors.GREY_700)
                flow_s = core.format_flow(s['main_flow'])
                vr_s = '%.2f' % s['vr'] if s['vr'] else '-'
                tr_s = '%.2f%%' % s['turnover'] if s['turnover'] else '-'
                pe_s = '%.1f' % s['pe'] if s['pe'] else '--'

                result_list.controls.append(
                    ft.Card(
                        elevation=1,
                        content=ft.Container(
                            padding=10,
                            ink=True,
                            content=ft.Column([
                                ft.Row([
                                    ft.Text('%d. %s %s' % (i + 1, s['code'], s['name']),
                                            size=15, weight=ft.FontWeight.BOLD),
                                    ft.Text('评分 %.1f' % s['score'], color=colors.ORANGE_800,
                                            weight=ft.FontWeight.BOLD),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                                ft.Row([
                                    ft.Text('现价 %.2f' % s['price'], size=13),
                                    ft.Text('涨幅 %+.2f%%' % chg, size=13, color=chg_color),
                                    ft.Text('量比 %s' % vr_s, size=13),
                                    ft.Text('换手 %s' % tr_s, size=13),
                                    ft.Text('PE %s' % pe_s, size=13, color=colors.GREY_600),
                                ], wrap=True),
                                ft.Row([
                                    ft.Text('主力净流入 %s' % flow_s, size=12, color=colors.RED_700),
                                    ft.Text('行业 %s' % s['industry'], size=12, color=colors.GREY_600),
                                ], wrap=True),
                            ]),
                        ),
                    )
                )
            result_count.value = '扫描完成：%d 只符合条件，展示前 %d 只' % (len(results), n)
        except Exception as e:
            result_count.value = '扫描出错: %s' % e
        finally:
            progress.visible = False
            scan_btn.disabled = False
            page.update()

    def on_scan(e):
        threading.Thread(target=do_scan, daemon=True).start()

    scan_btn.on_click = on_scan

    page.add(
        title,
        subtitle,
        ft.Divider(height=1),
        market_label,
        industry_label,
        ft.Row([scan_btn, cfg_btn]),
        cfg_panel,
        progress,
        progress_text,
        ft.Divider(height=1),
        result_count,
        result_list,
    )


if __name__ == '__main__':
    ft.app(target=main)
