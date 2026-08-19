(function () {
    function setupCanvas(canvas) {
        if (!canvas) return null;
        const rect = canvas.getBoundingClientRect();
        const ratio = window.devicePixelRatio || 1;
        canvas.width = Math.max(320, rect.width * ratio);
        canvas.height = Math.max(240, (rect.height || 320) * ratio);
        const ctx = canvas.getContext('2d');
        ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
        return { ctx, width: rect.width, height: rect.height || 320 };
    }

    function priceChart(candles) {
        const canvas = document.getElementById('priceChart');
        const ready = setupCanvas(canvas);
        if (!ready) return;
        const data = (candles || []).filter(c => Number.isFinite(Number(c.open)) && Number.isFinite(Number(c.high)) && Number.isFinite(Number(c.low)) && Number.isFinite(Number(c.close))).slice(-80);
        if (!data.length) {
            const {ctx, width, height} = ready;
            ctx.clearRect(0,0,width,height);
            ctx.fillStyle = '#7f8ca3'; ctx.font = '13px Segoe UI';
            ctx.fillText('Waiting for live market candles…', 18, Math.max(30, height / 2));
            return;
        }
        const { ctx, width, height } = ready;
        ctx.clearRect(0, 0, width, height);
        const pad = { top: 20, right: 70, bottom: 30, left: 10 };
        const hi = Math.max(...data.map(c => c.high));
        const lo = Math.min(...data.map(c => c.low));
        const range = hi - lo || 1;
        const xStep = (width - pad.left - pad.right) / data.length;
        const y = value => pad.top + (hi - value) / range * (height - pad.top - pad.bottom);

        ctx.strokeStyle = 'rgba(255,255,255,.08)';
        ctx.lineWidth = 1;
        for (let i = 0; i < 5; i++) {
            const gy = pad.top + i * (height - pad.top - pad.bottom) / 4;
            ctx.beginPath(); ctx.moveTo(pad.left, gy); ctx.lineTo(width - pad.right, gy); ctx.stroke();
        }

        data.forEach((c, i) => {
            const x = pad.left + i * xStep + xStep / 2;
            const openY = y(c.open), closeY = y(c.close), highY = y(c.high), lowY = y(c.low);
            const up = c.close >= c.open;
            ctx.strokeStyle = up ? '#00ff95' : '#ff4d6d';
            ctx.fillStyle = up ? '#00ff95' : '#ff4d6d';
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(x, highY); ctx.lineTo(x, lowY); ctx.stroke();
            const bodyTop = Math.min(openY, closeY);
            const bodyHeight = Math.max(1.5, Math.abs(closeY - openY));
            ctx.fillRect(x - Math.max(2, xStep * .28), bodyTop, Math.max(3, xStep * .56), bodyHeight);
        });

        ctx.fillStyle = '#9aa7b8';
        ctx.font = '12px Segoe UI';
        ctx.fillText(hi.toLocaleString(undefined, { maximumFractionDigits: 4 }), width - pad.right + 8, pad.top + 4);
        ctx.fillText(lo.toLocaleString(undefined, { maximumFractionDigits: 4 }), width - pad.right + 8, height - pad.bottom);
    }

    function equityChart(points) {
        const canvas = document.getElementById('equityChart');
        const ready = setupCanvas(canvas);
        if (!ready) return;
        if (!points?.length) {
            const {ctx, width, height} = ready;
            ctx.clearRect(0,0,width,height);
            ctx.fillStyle = '#7f8ca3'; ctx.font = '13px Segoe UI';
            ctx.fillText('Equity curve will appear when PQI starts scanning.', 18, Math.max(30, height / 2));
            return;
        }
        const { ctx, width, height } = ready;
        ctx.clearRect(0, 0, width, height);
        const values = points.map(p => Number(p.value));
        const hi = Math.max(...values), lo = Math.min(...values), range = hi - lo || 1;
        const pad = 30;
        const x = i => pad + i * (width - pad * 2) / Math.max(1, values.length - 1);
        const y = v => pad + (hi - v) / range * (height - pad * 2);
        ctx.strokeStyle = 'rgba(0,245,255,.25)'; ctx.lineWidth = 2; ctx.beginPath();
        values.forEach((v, i) => i ? ctx.lineTo(x(i), y(v)) : ctx.moveTo(x(i), y(v)));
        ctx.stroke();
        ctx.lineTo(x(values.length - 1), height - pad); ctx.lineTo(x(0), height - pad); ctx.closePath();
        ctx.fillStyle = 'rgba(0,245,255,.08)'; ctx.fill();
        ctx.fillStyle = '#9aa7b8'; ctx.font = '12px Segoe UI';
        ctx.fillText(`$${hi.toFixed(2)}`, 5, y(hi) + 4); ctx.fillText(`$${lo.toFixed(2)}`, 5, y(lo) + 4);
    }

    function renderTimeframe(state, timeframe) {
        const tf = timeframe || '1h';
        const candles = state?.candles_by_timeframe?.[tf] || state?.candles || [];
        priceChart(candles);
    }

    window.PQICharts = { priceChart, equityChart, renderTimeframe };
    window.addEventListener('resize', () => {
        if (window.__pqiLastState) {
            renderTimeframe(window.__pqiLastState, document.getElementById("chart-timeframe")?.value || "1h");
            equityChart(window.__pqiLastState.equity_curve || []);
        }
    });
})();
