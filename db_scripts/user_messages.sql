-- User messages table for storing contact submissions
IF OBJECT_ID('dbo.user_messages', 'U') IS NOT NULL
    DROP TABLE dbo.user_messages;
GO

CREATE TABLE dbo.user_messages (
    message_id INT IDENTITY(1,1) PRIMARY KEY,
    name NVARCHAR(100) NOT NULL,
    email NVARCHAR(150) NOT NULL,
    subject NVARCHAR(200) NOT NULL,
    message NVARCHAR(MAX) NOT NULL,
    response NVARCHAR(MAX) NULL,
    status NVARCHAR(20) NOT NULL CONSTRAINT DF_user_messages_status DEFAULT 'New',
    created_at DATETIME2 NOT NULL CONSTRAINT DF_user_messages_created DEFAULT GETDATE(),
    replied_at DATETIME2 NULL
);
GO

CREATE NONCLUSTERED INDEX IX_user_messages_status_created
ON dbo.user_messages(status, created_at DESC);
GO

