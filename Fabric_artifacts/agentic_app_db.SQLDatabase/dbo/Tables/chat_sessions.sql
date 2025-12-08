CREATE TABLE [dbo].[chat_sessions] (
    [session_id]         VARCHAR (255) NOT NULL,
    [user_id]            VARCHAR (255) NOT NULL,
    [title]              VARCHAR (500) NULL,
    [total_agents_used]  INT           DEFAULT ((0)) NULL,
    [primary_agent_type] VARCHAR (100) NULL,
    [created_at]         DATETIME2 (7) DEFAULT (getdate()) NULL,
    [updated_at]         DATETIME2 (7) DEFAULT (getdate()) NULL,
    PRIMARY KEY CLUSTERED ([session_id] ASC)
);


GO

