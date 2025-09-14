-- Create schema and tables if they do not exist
CREATE SCHEMA IF NOT EXISTS public;

CREATE TABLE IF NOT EXISTS public.gold_prices (
  id BIGSERIAL PRIMARY KEY,
  source TEXT NOT NULL,
  price NUMERIC(18,6) NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_gold_prices_fetched_at ON public.gold_prices(fetched_at);
CREATE INDEX IF NOT EXISTS idx_gold_prices_source ON public.gold_prices(source);
