import json
import time
import urllib.request

APP_NAME = '智选股 v2.0'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'http://quote.eastmoney.com/',
}

HOSTS = ['http://push2.eastmoney.com', 'http://push2delay.eastmoney.com']
HOST_INDEX = 0

DEFAULT_CFG = {
    'max_price': 35.0,
    'min_chg': 3.0,
    'max_chg': 20.0,
    'min_vr': 1.0,
    'min_tr': 3.0,
    'max_tr': 25.0,
    'min_flow': 0,
    'exclude_kcb': True,
    'exclude_bj': True,
    'top_n': 30,
}


def _fetch(url, timeout=15, retries=3):
    global HOST_INDEX
    last_err = None
    for _ in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            last_err = e
            time.sleep(1.0)
    old = HOSTS[HOST_INDEX]
    new = HOSTS[1 - HOST_INDEX]
    url2 = url.replace(old, new)
    HOST_INDEX = 1 - HOST_INDEX
    for _ in range(retries):
        try:
            req = urllib.request.Request(url2, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except Exception as e:
            last_err = e
            time.sleep(1.0)
    raise Exception('网络请求失败: %s' % last_err)


def _query(path, params, timeout=15):
    url = HOSTS[HOST_INDEX] + path + '?' + '&'.join('%s=%s' % (k, v) for k, v in params.items())
    return _fetch(url, timeout=timeout)


def get_market_snapshot(progress_cb=None):
    params = {
        'pn': 1, 'pz': 100, 'po': 1, 'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281', 'fltt': 2, 'invt': 2,
        'fid': 'f3', 'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',
        'fields': 'f2,f3,f5,f6,f8,f9,f10,f12,f14,f62,f184,f100',
    }
    all_data = []
    page = 1
    total = 0
    while True:
        params['pn'] = page
        data = _query('/api/qt/clist/get', params)
        if not data or not data.get('data'):
            break
        total = data['data'].get('total', 0) or 0
        diff = data['data'].get('diff', []) or []
        all_data.extend(diff)
        if progress_cb:
            progress_cb(len(all_data), total)
        if len(all_data) >= total or not diff:
            break
        page += 1
        time.sleep(0.35)
    return all_data


def get_index_snapshot():
    indices = {
        '1.000001': '上证指数', '0.399001': '深证成指', '0.399006': '创业板指',
        '1.000300': '沪深300', '1.000905': '中证500', '1.000016': '上证50',
    }
    results = {}
    for secid, name in indices.items():
        url = (HOSTS[HOST_INDEX] + '/api/qt/stock/get?secid=' + secid +
               '&fltt=2&invt=2&fields=f43,f170,f169,f58')
        data = _fetch(url, timeout=8)
        if data and data.get('data'):
            d = data['data']
            results[name] = {
                'price': d.get('f43'),
                'change_pct': d.get('f170'),
                'change_amount': d.get('f169'),
                'volume': d.get('f58'),
            }
    return results


def get_industry_rank():
    params = {
        'pn': 1, 'pz': 20, 'po': 1, 'np': 1,
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281', 'fltt': 2, 'invt': 2,
        'fid': 'f3', 'fs': 'm:90+t:2', 'fields': 'f12,f14,f3,f62',
    }
    data = _query('/api/qt/clist/get', params, timeout=10)
    if data and data.get('data'):
        return data['data'].get('diff', []) or []
    return []


def _calc_score(st):
    flow = st.get('main_flow') or 0
    flow_score = min(40, max(0, flow) / 10000000.0 * 40)
    vr = st.get('vr') or 1
    vr_score = min(20, max(0, (vr - 1)) / 7.0 * 20)
    tr = st.get('turnover') or 0
    tr_score = min(20, max(0, (tr - 1.2)) / 10.8 * 20)
    chg = st.get('change_pct') or 0
    chg_score = min(20, max(0, chg) / 2.2 * 20)
    st['score'] = round(flow_score + vr_score + tr_score + chg_score, 1)


def _fnum(v):
    if v is None or v == '-' or v == '':
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def filter_stocks(stocks, cfg):
    results = []
    min_flow_yuan = (cfg.get('min_flow') or 0) * 10000
    for s in stocks:
        code = str(s.get('f12', ''))
        if not code:
            continue
        name = s.get('f14', '') or ''
        if 'ST' in name or '退' in name:
            continue
        if cfg.get('exclude_kcb') and (code.startswith('688') or code.startswith('689')):
            continue
        if cfg.get('exclude_bj') and (code.startswith('8') or code.startswith('4')):
            continue
        price = _fnum(s.get('f2'))
        change_pct = _fnum(s.get('f3'))
        turnover = _fnum(s.get('f8'))
        vr = _fnum(s.get('f10'))
        pe = _fnum(s.get('f9'))
        main_flow = _fnum(s.get('f62')) or 0
        main_flow_pct = _fnum(s.get('f184'))
        industry = s.get('f100') or ''
        if price is None or change_pct is None:
            continue
        if price > cfg.get('max_price', 999):
            continue
        if change_pct < cfg.get('min_chg', -99):
            continue
        if change_pct > cfg.get('max_chg', 99):
            continue
        if main_flow < min_flow_yuan:
            continue
        if vr is not None and vr < cfg.get('min_vr', 0):
            continue
        if turnover is not None:
            if turnover < cfg.get('min_tr', 0):
                continue
            if (cfg.get('max_tr') or 0) and turnover > cfg.get('max_tr', 99):
                continue
        st = {
            'code': code, 'name': name, 'price': price, 'change_pct': change_pct,
            'main_flow': main_flow, 'main_flow_pct': main_flow_pct, 'vr': vr,
            'turnover': turnover, 'pe': pe, 'industry': industry,
        }
        _calc_score(st)
        results.append(st)
    results.sort(key=lambda x: x.get('score', 0), reverse=True)
    return results


def judge_market(index_data):
    sh = index_data.get('上证指数')
    if not sh:
        return ('数据获取中', '请稍后重试')
    pct = sh.get('change_pct')
    if pct is None:
        return ('数据获取中', '请稍后重试')
    if pct < -0.5:
        return ('偏空', '建议空仓或轻仓(<30%)，仅关注最强资金票')
    if pct < -0.2:
        return ('偏弱', '建议轻仓(30%-50%)，严选主力净流入票')
    if pct > 0.8:
        return ('偏强', '可积极(70%-100%)，但避免追高已大涨个股')
    if pct > 0.3:
        return ('偏多', '可中等仓位(50%-70%)，优选资金+量能共振票')
    return ('震荡', '中等仓位(40%-60%)，精选个股、快进快出')


def format_flow(flow):
    if flow is None:
        return '-'
    if abs(flow) >= 100000000:
        return '%.2f亿' % (flow / 100000000)
    if abs(flow) >= 10000:
        return '%.0f万' % (flow / 10000)
    return '%.0f' % flow
