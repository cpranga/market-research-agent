-- Optional seed data for testing and demos

INSERT INTO raw_trades (symbol, ts, price, size, source)
VALUES
    ('AAPL', NOW() - INTERVAL '5 min', 189.12, 50, 'demo'),
    ('AAPL', NOW() - INTERVAL '4 min', 189.35, 30, 'demo'),
    ('MSFT', NOW() - INTERVAL '3 min', 331.25, 10, 'demo');

INSERT INTO context_market (window_start, window_end, spx_return, vix_level, risk_flag)
VALUES
    (NOW() - INTERVAL '15 min', NOW(), 0.0012, 13.7, 'low');
