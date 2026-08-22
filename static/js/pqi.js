(function () {
    if (window.__PQI_JS_INITIALIZED) return;
    window.__PQI_JS_INITIALIZED = true;

    const $ = id => document.getElementById(id);
    const money = v => `$${Number(v || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    let capitalDirty = false;
    let marketRetryTimer = null;
    // Add Trial enters a configuration-only flow. No new session is created
    // until ENGAGE PQI is pressed.
    let pendingNewSession = false;
    let pendingTrialConfig = null;
    const pageMode = new URLSearchParams(window.location.search).get('mode') || '';

    async function json(url, options = {}) {
        const opts = { ...options, headers: { ...(options.headers || {}) } };
        if ((opts.method || 'GET').toUpperCase() !== 'GET') {
            const token = document.querySelector('meta[name="csrf-token"]')?.content;
            if (token) opts.headers['X-CSRFToken'] = token;
        }
        const response = await fetch(url, opts);
        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.error || data.message || `Request failed (${response.status})`);
        return data;
    }

    function set(id, value) { const el = $(id); if (el) el.textContent = value ?? '--'; }

    function showFeedback(type, message) {
        const panel = document.querySelector('.market-control-panel');
        if (!panel) return;
        let box = $('pqi-feedback');
        if (!box) {
            box = document.createElement('div');
            box.id = 'pqi-feedback';
            panel.appendChild(box);
        }
        box.className = `pqi-feedback ${type}`;
        box.innerHTML = `<strong>${type === 'success' ? 'SUCCESS' : type === 'warning' ? 'CHECK REQUIRED' : 'ERROR'}</strong><span>${message}</span>`;
        box.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }

    function showTrialGuide(activeStep = 1, message = '') {
        const panel = document.querySelector('.market-control-panel');
        if (!panel || pageMode === 'live') return;
        let guide = $('pqi-trial-guide');
        if (!guide) {
            guide = document.createElement('div');
            guide.id = 'pqi-trial-guide';
            guide.className = 'pqi-trial-guide';
            const heading = panel.querySelector('.section-heading');
            heading?.insertAdjacentElement('afterend', guide);
        }
        const steps = [
            ['1', 'Configure', 'Select exchange, market type, trading pair and PQI capital.'],
            ['2', 'Apply', 'Click APPLY MARKET to validate and save the configuration.'],
            ['3', 'Engage', 'Click ENGAGE PQI to create and start the new trial session.']
        ];
        guide.innerHTML = `<div class="pqi-guide-title"><strong>START A NEW PQI TRIAL</strong><span>${message || 'Follow these three steps. Your existing sessions remain untouched.'}</span></div><div class="pqi-guide-steps">${steps.map(([n,title,text],i) => `<div class="pqi-guide-step ${activeStep === i+1 ? 'active' : activeStep > i+1 ? 'done' : ''}"><b>${n}</b><div><strong>${title}</strong><small>${text}</small></div></div>`).join('')}</div>`;
    }

    function populateMarkets(markets) {
        const select = $('market-select');
        if (!select) return;
        const current = pendingNewSession
            ? (pendingTrialConfig?.market || window.__pqiSelectedMarket || select.value)
            : (select.value || window.__pqiSelectedMarket);
        const clean = [...new Set((markets || []).filter(Boolean))];
        select.innerHTML = '';
        if (!clean.length) {
            const opt = document.createElement('option');
            opt.value = 'BTCUSDT'; opt.textContent = 'Loading pairs...';
            select.appendChild(opt);
            return;
        }
        clean.slice(0, 500).forEach(symbol => {
            const opt = document.createElement('option');
            opt.value = symbol; opt.textContent = symbol;
            select.appendChild(opt);
        });
        const wanted = current && clean.includes(current)
            ? current
            : (pendingNewSession ? clean[0] : (clean.includes('BTCUSDT') ? 'BTCUSDT' : clean[0]));
        select.value = wanted;
        window.__pqiSelectedMarket = wanted;
        if (pendingNewSession && !pendingTrialConfig) pendingTrialConfig = {market: wanted};
    }

    async function loadMarkets() {
        const exchange = $('exchange-select')?.value || 'binance';
        const marketType = $('market-type-select')?.value || 'spot';
        try {
            const data = await json(`/api/pqi/markets?exchange=${encodeURIComponent(exchange)}&market_type=${encodeURIComponent(marketType)}`);
            populateMarkets(data.markets || []);
            if ((data.markets || []).length) {
                set('market-feed-error', '');
                if (marketRetryTimer) { clearInterval(marketRetryTimer); marketRetryTimer = null; }
                await loadPreview();
            } else {
                set('market-feed-error', 'No trading pairs returned. Retrying market discovery...');
                scheduleMarketRetry();
            }
        } catch (e) {
            set('market-feed-error', `Market pairs unavailable: ${e.message}`);
            scheduleMarketRetry();
        }
    }

    function scheduleMarketRetry() {
        if (marketRetryTimer) return;
        marketRetryTimer = setInterval(loadMarkets, 8000);
    }

    async function loadPreview() {
        const select = $('market-select');
        if (!select) return;
        const symbol = select.value || 'BTCUSDT';
        if (symbol === 'BTCUSDT' && select.options.length === 1 && select.options[0].textContent.includes('Loading')) return;
        const exchange = $('exchange-select')?.value || 'binance';
        const marketType = $('market-type-select')?.value || 'spot';
        try {
            const data = await json(`/api/pqi/market-data?exchange=${encodeURIComponent(exchange)}&market_type=${encodeURIComponent(marketType)}&symbol=${encodeURIComponent(symbol)}`);
            const t = data.ticker || {};
            set('market-price', t.last ? Number(t.last).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-bid', t.bid ? Number(t.bid).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-ask', t.ask ? Number(t.ask).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-high', t.high ? Number(t.high).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-low', t.low ? Number(t.low).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-volume', money(t.volume));
            set('market-change', t.percentage == null ? '--' : `${Number(t.percentage).toFixed(2)}%`);
            set('market-spread', t.bid && t.ask ? Number(t.ask - t.bid).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-connection', t.last ? 'CONNECTED' : 'NO DATA');
            if (window.PQICharts) window.PQICharts.priceChart(data.candles || []);
        } catch (e) {
            set('market-connection', 'DISCONNECTED');
            set('market-feed-error', `Market feed unavailable: ${e.message}`);
        }
    }

    async function loadCapital() {
        try {
            const data = await json('/api/pqi/capital');
            set('capital-available', money(data.available));
            set('capital-mode', data.mode === 'trial' ? 'PAPER CAPITAL' : 'EXCHANGE CAPITAL');
            if (pageMode === 'live' && data.mode === 'live') {
                const exchangeSelect = $('exchange-select');
                const marketTypeSelect = $('market-type-select');
                if (exchangeSelect && data.exchange) { exchangeSelect.value = data.exchange; exchangeSelect.disabled = true; }
                if (marketTypeSelect && data.market_type) { marketTypeSelect.value = data.market_type; marketTypeSelect.disabled = true; }
            }
            const input = $('capital-input');
            if (input && !capitalDirty && document.activeElement !== input) input.value = data.selected || '';
            const liveHint = $('capital-hint');
            if (liveHint) liveHint.textContent = data.mode === 'trial'
                ? 'Live public market data · paper funds · minimum $10.'
                : `Connected exchange · available: ${money(data.available)} · ${data.can_trade ? 'trading authorized' : 'analysis only until trading is authorized'}.`;
        } catch (e) { set('capital-hint', e.message); }
    }

    async function configure() {
        const capital = Number($('capital-input')?.value);
        const market = pendingNewSession
            ? (pendingTrialConfig?.market || $('market-select')?.value || '')
            : ($('market-select')?.value || '');
        if (!market) throw new Error('Select a trading pair before applying the configuration.');
        if (!Number.isFinite(capital) || capital < 10) throw new Error('Minimum trading capital is $10.');
        return json('/api/pqi/config', {
            method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
            body: JSON.stringify({
                exchange: $('exchange-select')?.value || 'binance',
                market,
                market_type: $('market-type-select')?.value || 'spot',
                capital,
                mode: pageMode === 'live' ? 'live' : 'trial',
                new_session: pendingNewSession
            })
        });
    }

    async function engage(options = {}) {
        const btn = $('engage-pqi');
        const createNew = options.newSession === true || pendingNewSession;
        try {
            const capital = Number($('capital-input')?.value);
            const market = pendingNewSession
                ? (pendingTrialConfig?.market || $('market-select')?.value || '')
                : ($('market-select')?.value || '');
            if (!market) throw new Error('Select a trading pair before engaging PQI.');
            if (!Number.isFinite(capital) || capital < 10) throw new Error('Select trading capital of at least $10.');
            btn && (btn.disabled = true, btn.textContent = pageMode === 'live' ? 'STARTING LIVE PQI...' : 'STARTING MARKET ENGINE...');
            const data = await json('/api/pqi/engage', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    exchange: $('exchange-select')?.value || 'binance',
                    market,
                    market_type: $('market-type-select')?.value || 'spot',
                    capital,
                    mode: pageMode === 'live' ? 'live' : 'trial',
                    new_session: createNew
                })
            });
            capitalDirty = false;
            pendingNewSession = false;
            pendingTrialConfig = null;
            showFeedback('success', pageMode === 'live'
                ? 'Live PQI has been engaged. The selected PQI capital will continue to be used for the next trade while realised PnL remains on the connected exchange account.'
                : 'PQI trial engaged successfully. Paper PnL will remain preserved in the trial portfolio while the selected PQI capital is reused for the next trade.');
            await loadState();
            await loadSessions();
            return data;
        } catch (e) {
            showFeedback('error', e.message);
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = pageMode === 'live' ? 'START LIVE PQI' : 'ENGAGE PQI'; }
        }
    }

    async function addTrialSession() {
        if (pageMode === 'live') {
            window.location.href = '/trading';
            return;
        }
        if (!window.__pqiLastState || window.__pqiLastState.mode !== 'trial') return;

        // Do not create/engage anything here. Put the existing market controls
        // into "new session" mode and let the user choose the configuration.
        pendingNewSession = true;
        pendingTrialConfig = null;
        showTrialGuide(1);
        showFeedback('warning', 'Choose the exchange, market type, pair and capital first. Nothing has been started yet.');
        await loadMarkets();
        const panel = document.querySelector('.market-control-panel');
        panel?.scrollIntoView({behavior: 'smooth', block: 'center'});
        $('market-select')?.focus();
    }

    async function command(url) {
        try { await json(url, {method: 'POST'}); await loadState(); await loadSessions(); } catch (e) { alert(e.message); }
    }

    async function selectSession(sessionId) {
        try {
            await json('/api/pqi/session/select', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: sessionId})
            });
            await loadState();
            await loadSessions();
            await loadCapital();
        } catch (e) { alert(e.message); }
    }

    function renderSessions(items, meta = {}) {
        const host = $('pqi-session-list');
        if (!host) return;
        const max = Number(meta.max_active_sessions || 4);
        const count = Number(meta.active_session_count ?? items.length);
        const remaining = Math.max(0, max - count);
        set('pqi-session-capacity', `${count} / ${max} ACTIVE`);
        const addButton = $('add-trial-pqi');
        if (addButton) {
            addButton.disabled = count >= max;
            addButton.title = count >= max
                ? `Maximum of ${max} active PQI sessions reached.`
                : `Open another PQI session (${remaining} slot${remaining === 1 ? '' : 's'} available).`;
        }
        host.innerHTML = '';
        if (!items.length) {
            host.innerHTML = '<span class="session-empty">No active PQI sessions</span>';
            return;
        }
        items.forEach(item => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `pqi-session-tab${item.selected ? ' active' : ''}`;
            const pairs = (item.pairs || []).join(', ') || '--';
            button.innerHTML = `<span>${item.mode === 'live' ? 'LIVE' : 'TRIAL'} · ${item.exchange.toUpperCase()}</span><strong>${pairs}</strong><small>${Number(item.confidence || 0).toFixed(1)}% · ${item.decision || 'WAITING'}</small>`;
            button.addEventListener('click', () => selectSession(item.id));
            host.appendChild(button);
        });
    }

    async function loadSessions() {
        try {
            const data = await json('/api/pqi/sessions');
            renderSessions(data.sessions || [], data);
        } catch (e) { console.error('PQI sessions:', e); }
    }

    async function loadState() {
        try {
            const state = await json('/api/pqi/state');
            window.__pqiLastState = state;
            set('pqi-status', state.status); set('exchange', state.exchange); set('market', state.market);
            set('decision', state.current_decision); set('confidence', `${Number(state.confidence || 0).toFixed(2)}%`);
            set('regime', state.market_regime || '--'); set('positions', state.open_positions);
            set('portfolio', money(state.portfolio_value)); set('starting-capital', money(state.starting_capital));
            set('available-capital', money(state.available_capital)); set('daily-pnl', money(state.daily_pnl));
            set('live-account-balance', state.live_account_balance != null ? money(state.live_account_balance) : '--');
            set('live-realised-pnl', state.live_realised_pnl != null ? money(state.live_realised_pnl) : '--');
            set('nextscan', state.next_scan ? new Date(state.next_scan).toLocaleTimeString() : '--'); set('task', state.current_task);
            set('signals', state.signals_analysed); set('trades', state.trades_today); set('winrate', `${Number(state.win_rate || 0).toFixed(2)}%`);
            set('risk', `${Number(state.risk_exposure || 0).toFixed(2)}%`);
            set('drawdown', state.starting_capital ? `${Math.max(0, ((state.starting_capital - state.portfolio_value) / state.starting_capital) * 100).toFixed(2)}%` : '0%');
            set('exposure', state.open_positions ? `${Number(state.risk_exposure || 0).toFixed(2)}%` : '0%');
            set('leverage', state.mode === 'live' && state.market_type === 'futures' ? 'PQI' : '1x');
            set('total-return', state.starting_capital ? `${(((state.portfolio_value - state.starting_capital) / state.starting_capital) * 100).toFixed(2)}%` : '0%');
            set('health', state.status === 'ERROR' ? 'DEGRADED' : (state.market_status === 'ONLINE' ? 'OPTIMAL' : 'STANDBY'));
            set('scanner-update', state.last_market_update ? new Date(state.last_market_update).toLocaleTimeString() : '--');
            set('decision-update', state.last_market_update ? new Date(state.last_market_update).toLocaleTimeString() : '--');
            set('learning-update', state.last_market_update ? new Date(state.last_market_update).toLocaleTimeString() : '--');
            set('risk-update', state.last_market_update ? new Date(state.last_market_update).toLocaleTimeString() : '--');
            set('market-price', state.last_price ? Number(state.last_price).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-change', state.change_percent_24h == null ? '--' : `${Number(state.change_percent_24h).toFixed(2)}%`);
            set('market-bid', state.bid ? Number(state.bid).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-ask', state.ask ? Number(state.ask).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-volume', money(state.volume_24h)); set('market-spread', state.spread == null ? '--' : Number(state.spread).toLocaleString(undefined, {maximumFractionDigits: 8}));
            set('market-high', state.high_24h ? Number(state.high_24h).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-low', state.low_24h ? Number(state.low_24h).toLocaleString(undefined, {maximumFractionDigits: 8}) : '--');
            set('market-connection', state.connection_status); set('market-feed-error', state.market_status === 'ERROR' ? state.current_decision : '');
            if ($('market-select') && state.symbol && !pendingNewSession) {
                $('market-select').value = state.symbol;
                window.__pqiSelectedMarket = state.symbol;
            }
            if (window.PQICharts) { window.PQICharts.priceChart(state.candles || []); window.PQICharts.equityChart(state.equity_curve || []); }
            updateIntelligence(state); updatePortfolio(state); updateTrading(state);
            const signalRows = $('signals-table');
            if (signalRows) signalRows.innerHTML = (state.activity || []).slice(0, 20).map(x => `<tr><td>${new Date(x.time).toLocaleTimeString()}</td><td>${state.market || '--'}</td><td>${Number(state.confidence || 0).toFixed(2)}%</td><td>${state.current_decision || '--'}</td><td>${state.market_status || '--'}</td></tr>`).join('');
            const reportRows = $('report-table');
            if (reportRows) reportRows.innerHTML = (state.execution_log || []).slice(0, 20).map(x => `<tr><td>${new Date(x.time).toLocaleDateString()}</td><td>${state.trades_today || 0}</td><td>${Number(state.win_rate || 0).toFixed(2)}%</td><td>${money(x.pnl || 0)}</td><td>${state.starting_capital ? (((state.portfolio_value-state.starting_capital)/state.starting_capital)*100).toFixed(2)+'%' : '0%'}</td></tr>`).join('');
        } catch (e) { console.error('PQI state:', e); }
    }

    function updateIntelligence(state) {
        const i = state.intelligence || {};
        set('trend', i.trend); set('momentum', i.momentum); set('volatility', i.volatility); set('liquidity', i.volume);
        set('signal', i.signal); set('entry', i.entry ? money(i.entry) : '--'); set('sl', i.stop_loss ? money(i.stop_loss) : '--');
        set('tp', i.take_profit ? money(i.take_profit) : '--'); set('rr', i.reward_ratio ? Number(i.reward_ratio).toFixed(2) : '--'); set('intelligence-reason', i.reason);
    }

    function updatePortfolio(state) {
        set('portfolio', money(state.mode === 'live' && state.live_account_balance != null ? state.live_account_balance : state.portfolio_value));
        set('starting-capital', money(state.starting_capital));
        set('available-capital', money(state.available_capital));
        set('realised-pnl', money(state.realised_pnl));
        set('unrealised-pnl', money(state.unrealised_pnl));
        const position = state.paper_position, body = $('positions-table');
        if (body) {
            const rows = (state.session_pairs || []).filter(p => p.status === 'OPEN');
            if (body.closest('.dashboard')) {
                body.innerHTML = position ? `<tr><td>${position.symbol}</td><td>${position.side || '--'}</td><td>${money(position.entry_price)}</td><td>${money(position.mark_price)}</td><td>${money(position.pnl)}</td></tr>` : '<tr><td colspan="5">No active PQI position.</td></tr>';
            } else {
                body.innerHTML = rows.length ? rows.map(p => `<tr><td>${p.symbol}</td><td>${p.side || '--'}</td><td>${money(p.entry_price)}</td><td>${money(p.mark_price)}</td><td>${money(p.stop_loss)}</td><td>${money(p.take_profit)}</td><td>${money(p.pnl)}</td><td>${Number(p.quantity || 0).toFixed(6)}</td><td>${p.status}</td></tr>`).join('') : '<tr><td colspan="9">No open PQI positions.</td></tr>';
            }
        }
        const pairs = $('pair-performance-body');
        if (pairs) {
            const items = state.session_pairs || [];
            pairs.innerHTML = items.length ? items.slice().reverse().map(p => `<tr><td><strong>${p.symbol}</strong></td><td>${p.status || '--'}</td><td>${p.side || '--'}</td><td>${money(p.allocation)}</td><td>${p.entry_price ? money(p.entry_price) : '--'}</td><td>${p.stop_loss ? money(p.stop_loss) : '--'}</td><td>${p.take_profit ? money(p.take_profit) : '--'}</td><td>${money(p.pnl)}</td><td>${money(p.pair_balance)}</td></tr>`).join('') : '<tr><td colspan="9">No pair trade footprint yet.</td></tr>';
        }
        const footprints = $('trade-footprints-body');
        if (footprints) {
            const log = (state.execution_log || []).filter(x => x.status === 'PAPER OPEN' || x.status === 'PAPER CLOSE' || x.status === 'LIVE OPEN' || x.status === 'LIVE CLOSE');
            footprints.innerHTML = log.length ? log.slice(0, 20).map(x => `<tr><td>${new Date(x.time).toLocaleTimeString()}</td><td>${x.symbol || '--'}</td><td>${x.status || '--'}</td><td>${x.reason || '--'}</td><td>${x.entry_price ? money(x.entry_price) : '--'}</td><td>${x.stop_loss ? money(x.stop_loss) : '--'}</td><td>${x.take_profit ? money(x.take_profit) : '--'}</td><td>${money(x.pnl)}</td></tr>`).join('') : '<tr><td colspan="8">No SL/TP footprint recorded yet.</td></tr>';
        }
    }

    function updateTrading(state) {
        set('exec-status', state.status); set('exec-task', state.current_task); set('exec-decision', state.current_decision); set('exec-exchange', state.exchange); set('exec-market', state.market);
        set('exec-risk', state.connection_status === 'ERROR' ? 'BLOCKED' : (state.mode === 'live' ? (state.exchange_connected ? 'MONITORED' : 'CONNECTING') : 'PAPER'));
        const log = $('execution-log');
        if (log && state.execution_log) log.innerHTML = state.execution_log.map(x => `<tr><td>${new Date(x.time).toLocaleTimeString()}</td><td>${state.exchange}</td><td>${x.symbol || state.market}</td><td>${x.side || '--'}</td><td>${x.status || '--'}</td></tr>`).join('');

        const orders = $('orders-table');
        if (orders) {
            const entries = state.execution_log || [];
            orders.innerHTML = entries.length ? entries.slice(0, 30).map(x => `<tr><td>${new Date(x.time).toLocaleTimeString()}</td><td>${x.symbol || state.market || '--'}</td><td>${x.status || '--'}</td><td>${x.side || '--'}</td><td>${x.entry_price ? money(x.entry_price) : '--'}</td><td>${x.stop_loss ? money(x.stop_loss) : '--'}</td><td>${x.take_profit ? money(x.take_profit) : '--'}</td><td>${x.status || '--'}</td></tr>`).join('') : '<tr><td colspan="8">No PQI order events yet.</td></tr>';
        }

        set('risk', `${Number(state.risk_exposure || 0).toFixed(2)}%`);
        set('drawdown', `${Math.max(0, state.starting_capital ? ((state.starting_capital - state.portfolio_value) / state.starting_capital) * 100 : 0).toFixed(2)}%`);
        set('exposure', `${Number(state.risk_exposure || 0).toFixed(2)}%`);
        set('leverage', state.market_type === 'futures' ? 'Risk cap 20x' : '1x');
        set('risk-market', state.market || '--'); set('risk-market-type', (state.market_type || '--').toUpperCase()); set('risk-decision', state.current_decision || 'WAITING'); set('risk-open-positions', state.open_positions || 0); set('risk-reason', (state.intelligence || {}).reason || state.current_task || '--'); set('risk-status', state.status || 'WAITING');

        set('signals', state.signals_analysed || 0);
        set('signal-market', state.market || '--');
        const signalRows = $('signals-table');
        if (signalRows) {
            const signalEvents = (state.activity || []).filter(x => /confidence updated|signal|decision/i.test(String(x.message || '')));
            signalRows.innerHTML = signalEvents.length ? signalEvents.slice(0, 20).map(x => `<tr><td>${new Date(x.time).toLocaleTimeString()}</td><td>${state.market || '--'}</td><td>${Number(state.confidence || 0).toFixed(2)}%</td><td>${state.current_decision || '--'}</td><td>${state.market_status || '--'}</td></tr>`).join('') : '<tr><td colspan="5">No signal event recorded yet.</td></tr>';
        }

        const closed = (state.session_pairs || []).filter(p => p.status === 'CLOSED').length;
        const candles = state.candles || [];
        const first = candles[0]?.time, last = candles[candles.length - 1]?.time;
        set('test-period', first && last ? `${new Date(first).toLocaleDateString()} – ${new Date(last).toLocaleDateString()}` : '--');
        set('bt-return', 'NOT RUN'); set('bt-winrate', candles.length); set('bt-drawdown', state.market || '--'); set('bt-sharpe', closed); set('bt-score', candles.length ? 'READY' : 'WAITING');
        const bt = $('backtest-table');
        if (bt) bt.innerHTML = `<tr><td>${state.market || '--'}</td><td>${(state.market_type || '--').toUpperCase()}</td><td>${candles.length}</td><td>${closed}</td><td>${candles.length ? 'DATA READY' : 'WAITING'}</td></tr>`;
        set('backtest-note', candles.length ? `Historical market data is loaded for ${state.market || 'the active market'}. No backtest result is fabricated until a historical test is actually executed.` : 'Waiting for historical market data.');

        const closedPnls = (state.session_pairs || []).filter(p => p.status === 'CLOSED').map(p => Number(p.pnl || 0));
        const wins = closedPnls.filter(v => v > 0).reduce((a,b) => a+b, 0);
        const losses = Math.abs(closedPnls.filter(v => v < 0).reduce((a,b) => a+b, 0));
        const profitFactor = losses > 0 ? wins / losses : (wins > 0 ? '∞' : 0);
        const dd = Math.max(0, state.starting_capital ? ((state.starting_capital - state.portfolio_value) / state.starting_capital) * 100 : 0);
        set('total-return', `${state.starting_capital ? (((state.portfolio_value - state.starting_capital) / state.starting_capital) * 100).toFixed(2) : '0.00'}%`);
        set('winrate', `${Number(state.win_rate || 0).toFixed(2)}%`); set('trades', state.trades_today || 0); set('profit-factor', typeof profitFactor === 'string' ? profitFactor : Number(profitFactor).toFixed(2)); set('drawdown', `${dd.toFixed(2)}%`); set('health', state.status === 'ERROR' ? 'ERROR' : state.status === 'ACTIVE' ? 'ACTIVE' : state.status || 'WAITING');
        const report = $('report-table');
        if (report) report.innerHTML = `<tr><td>${new Date().toLocaleDateString()}</td><td>${state.trades_today || 0}</td><td>${Number(state.win_rate || 0).toFixed(2)}%</td><td>${money(state.daily_pnl || 0)}</td><td>${state.starting_capital ? (((state.portfolio_value-state.starting_capital)/state.starting_capital)*100).toFixed(2)+'%' : '0%'}</td></tr>`;
        set('report-note', `Live performance snapshot · ${state.market || '--'} · ${(state.market_type || '--').toUpperCase()} · ${state.status || 'WAITING'}`);
    }

    document.addEventListener('DOMContentLoaded', () => {
        if (!$('pqi-status') && !$('engage-pqi') && !$('market-select') && !$('confidence') && !$('portfolio')) return;
        $('engage-pqi')?.addEventListener('click', () => engage());
        $('add-trial-pqi')?.addEventListener('click', addTrialSession);
        $('pause-pqi')?.addEventListener('click', () => command('/api/pqi/pause'));
        $('stop-pqi')?.addEventListener('click', () => command('/api/pqi/stop'));
        $('configure-pqi')?.addEventListener('click', async () => {
            try {
                const result = await configure();
                if (pendingNewSession) {
                    pendingTrialConfig = result.applied || {
                        market: $('market-select')?.value || '',
                        exchange: $('exchange-select')?.value || 'binance',
                        market_type: $('market-type-select')?.value || 'spot',
                        capital: Number($('capital-input')?.value || 0)
                    };
                    window.__pqiSelectedMarket = pendingTrialConfig.market;
                    if ($('market-select')) $('market-select').value = pendingTrialConfig.market;
                    showTrialGuide(3, 'Configuration accepted. Review the values, then engage PQI to start the new session.');
                    showFeedback('success', `Configuration applied: ${pendingTrialConfig.exchange.toUpperCase()} · ${pendingTrialConfig.market} · ${pendingTrialConfig.market_type.toUpperCase()} · $${Number(pendingTrialConfig.capital).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}. Click ENGAGE PQI to start.`);
                } else {
                    await loadState();
                    showFeedback('success', 'PQI configuration applied successfully.');
                }
            } catch(e) {
                const validation = /select a trading pair|minimum trading capital|valid trading capital/i.test(e.message || '');
                showFeedback(validation ? 'warning' : 'error', e.message);
            }
        });
        $('exchange-select')?.addEventListener('change', async () => { capitalDirty = false; await loadMarkets(); await loadCapital(); });
        $('market-type-select')?.addEventListener('change', async () => { capitalDirty = false; await loadMarkets(); await loadCapital(); });
        $('market-select')?.addEventListener('change', () => {
            window.__pqiSelectedMarket = $('market-select').value;
            if (pendingNewSession) {
                pendingTrialConfig = {
                    ...(pendingTrialConfig || {}),
                    market: $('market-select').value,
                    exchange: $('exchange-select')?.value || 'binance',
                    market_type: $('market-type-select')?.value || 'spot',
                    capital: Number($('capital-input')?.value || 0)
                };
            }
            loadPreview();
        });
        $('capital-input')?.addEventListener('input', () => { capitalDirty = true; });
        document.querySelectorAll('.capital-preset').forEach(b => b.addEventListener('click', () => { const input=$('capital-input'); if(input){input.value=b.dataset.value; input.dispatchEvent(new Event('input',{bubbles:true}));} }));
        document.addEventListener('visibilitychange', () => { if (!document.hidden) { loadMarkets(); loadState(); loadCapital(); loadSessions(); } });
        loadMarkets(); loadCapital(); loadState(); loadSessions();
        setInterval(loadState, 1500); setInterval(loadSessions, 5000); setInterval(loadCapital, 5000);
        setInterval(() => { if (document.visibilityState === 'visible' && (!$('pqi-status') || $('pqi-status').textContent !== 'ACTIVE')) loadPreview(); }, 10000);
    });
})();
