(function () {
    if (window.__PQI_JS_INITIALIZED) return;
    window.__PQI_JS_INITIALIZED = true;

    const $ = id => document.getElementById(id);
    const money = v => `$${Number(v || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    let capitalDirty = false;
    let marketRetryTimer = null;

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

    function populateMarkets(markets) {
        const select = $('market-select');
        if (!select) return;
        const current = select.value || window.__pqiSelectedMarket;
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
        const wanted = current && clean.includes(current) ? current : (clean.includes('BTCUSDT') ? 'BTCUSDT' : clean[0]);
        select.value = wanted;
        window.__pqiSelectedMarket = wanted;
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
        marketRetryTimer = setInterval(async () => {
            await loadMarkets();
        }, 8000);
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
            const input = $('capital-input');
            if (input && !capitalDirty && document.activeElement !== input) input.value = data.selected || '';
            const liveHint = $('capital-hint');
            if (liveHint) liveHint.textContent = data.mode === 'trial' ? 'Live public market data · paper funds · minimum $10.' : `Available on exchange: ${money(data.available)} · minimum $10.`;
        } catch (e) { set('capital-hint', e.message); }
    }

    async function configure() {
        const capital = Number($('capital-input')?.value);
        if (!Number.isFinite(capital) || capital < 10) throw new Error('Minimum trading capital is $10.');
        const data = await json('/api/pqi/config', {
            method: 'POST', headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
            body: JSON.stringify({
                exchange: $('exchange-select')?.value || 'binance',
                market: $('market-select')?.value || 'BTCUSDT',
                market_type: $('market-type-select')?.value || 'spot',
                capital
            })
        });
        capitalDirty = false;
        return data;
    }

    async function engage() {
        const btn = $('engage-pqi');
        try {
            const capital = Number($('capital-input')?.value);
            if (!Number.isFinite(capital) || capital < 10) throw new Error('Select trading capital of at least $10.');
            btn && (btn.disabled = true, btn.textContent = 'STARTING MARKET ENGINE...');
            const data = await json('/api/pqi/engage', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    exchange: $('exchange-select')?.value || 'binance',
                    market: $('market-select')?.value || 'BTCUSDT',
                    market_type: $('market-type-select')?.value || 'spot',
                    capital
                })
            });
            capitalDirty = false;
            await loadState();
            await loadMarkets();
            return data;
        } catch (e) {
            alert(e.message);
        } finally {
            if (btn) { btn.disabled = false; btn.textContent = 'ENGAGE PQI'; }
        }
    }

    async function command(url) {
        try { await json(url, {method: 'POST'}); await loadState(); } catch (e) { alert(e.message); }
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
            if ($('market-select') && state.symbol) $('market-select').value = state.symbol;
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
        set('portfolio', money(state.portfolio_value)); set('starting-capital', money(state.starting_capital)); set('available-capital', money(state.available_capital));
        const position = state.paper_position, body = $('positions-table');
        if (body && body.closest('.dashboard') === null) body.innerHTML = position ? `<tr><td>${position.symbol}</td><td>${position.side}</td><td>${Number(position.quantity).toFixed(6)}</td><td>${money(position.entry_price)}</td><td>${money(position.mark_price)}</td><td>${money(position.pnl)}</td><td>OPEN</td></tr>` : '<tr><td colspan="7">No open PQI position.</td></tr>';
    }

    function updateTrading(state) {
        set('exec-status', state.status); set('exec-task', state.current_task); set('exec-decision', state.current_decision); set('exec-exchange', state.exchange); set('exec-market', state.market);
        set('exec-risk', state.connection_status === 'ERROR' ? 'BLOCKED' : 'MONITORED');
        const log = $('execution-log');
        if (log && state.execution_log) log.innerHTML = state.execution_log.map(x => `<tr><td>${new Date(x.time).toLocaleTimeString()}</td><td>${state.exchange}</td><td>${x.symbol || state.market}</td><td>${x.side || '--'}</td><td>${x.status || '--'}</td></tr>`).join('');
    }

    document.addEventListener('DOMContentLoaded', () => {
        if (!$('pqi-status') && !$('engage-pqi') && !$('market-select') && !$('confidence') && !$('portfolio')) return;
        $('engage-pqi')?.addEventListener('click', engage);
        $('pause-pqi')?.addEventListener('click', () => command('/api/pqi/pause'));
        $('stop-pqi')?.addEventListener('click', () => command('/api/pqi/stop'));
        $('configure-pqi')?.addEventListener('click', async () => { try { await configure(); await loadState(); } catch(e) { alert(e.message); } });
        $('exchange-select')?.addEventListener('change', async () => { capitalDirty = false; await loadMarkets(); await loadCapital(); });
        $('market-type-select')?.addEventListener('change', async () => { capitalDirty = false; await loadMarkets(); await loadCapital(); });
        $('market-select')?.addEventListener('change', () => { window.__pqiSelectedMarket = $('market-select').value; loadPreview(); });
        $('capital-input')?.addEventListener('input', () => { capitalDirty = true; });
        document.querySelectorAll('.capital-preset').forEach(b => b.addEventListener('click', () => { const input=$('capital-input') || $('trial-capital'); if(input){input.value=b.dataset.value; input.dispatchEvent(new Event('input',{bubbles:true}));} }));
        document.addEventListener('visibilitychange', () => { if (!document.hidden) { loadMarkets(); loadState(); loadCapital(); } });
        loadMarkets(); loadCapital(); loadState();
        setInterval(loadState, 1500); setInterval(loadCapital, 5000); setInterval(() => { if (document.visibilityState === 'visible' && (!$('pqi-status') || $('pqi-status').textContent !== 'ACTIVE')) loadPreview(); }, 10000);
    });
})();