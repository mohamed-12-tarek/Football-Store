-- Currency table for Football Store
-- This table stores currency information and exchange rates
-- Base currency: EGP (Egyptian Pound)

IF OBJECT_ID('dbo.currencies', 'U') IS NOT NULL
    DROP TABLE dbo.currencies;
GO

CREATE TABLE dbo.currencies (
    currency_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    code NVARCHAR(10) NOT NULL UNIQUE,
    symbol NVARCHAR(10) NOT NULL,
    exchange_rate DECIMAL(10,6) NOT NULL DEFAULT 1.0,
    is_active BIT NOT NULL DEFAULT 1,
    is_base BIT NOT NULL DEFAULT 0,
    created_at DATETIME2 NOT NULL DEFAULT GETDATE(),
    updated_at DATETIME2 NOT NULL DEFAULT GETDATE()
);
GO

-- Create nonclustered indexes
CREATE NONCLUSTERED INDEX IX_currencies_code
ON dbo.currencies(code, is_active);
GO

CREATE NONCLUSTERED INDEX IX_currencies_base
ON dbo.currencies(is_base, is_active);
GO

-- Insert default currencies
INSERT INTO dbo.currencies (name, code, symbol, exchange_rate, is_active, is_base)
VALUES
    ('Egyptian Pound', 'EGP', 'EGP', 1.000000, 1, 1),      -- Base currency
    ('US Dollar', 'USD', '$', 0.032000, 1, 0),
    ('Euro', 'EUR', 'EUR', 0.027000, 1, 0),
    ('British Pound', 'GBP', 'GBP', 0.023000, 1, 0),
    ('Saudi Riyal', 'SAR', 'SAR', 0.008500, 1, 0),
    ('UAE Dirham', 'AED', 'AED', 0.008700, 1, 0);
GO

PRINT '[OK] Currencies table created and seeded successfully';
GO
