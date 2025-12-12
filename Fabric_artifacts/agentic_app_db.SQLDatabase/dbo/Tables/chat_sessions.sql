CREATE TABLE [dbo].[chat_sessions] (
    [session_id]          VARCHAR (255)  NOT NULL,
    [user_id]             VARCHAR (255)  NOT NULL,
    [title]               VARCHAR (500)  NULL,
    [total_agents_used]   INT            DEFAULT ((0)) NULL,
    [agent_names_used]    NVARCHAR (MAX) NULL,
    [created_at]          DATETIME2 (7)  DEFAULT (getdate()) NULL,
    [updated_at]          DATETIME2 (7)  DEFAULT (getdate()) NULL,
    [session_duration_ms] INT            DEFAULT ((0)) NULL,
    PRIMARY KEY CLUSTERED ([session_id] ASC)
);


GO

