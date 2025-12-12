CREATE TABLE [dbo].[tool_usage] (
    [tool_call_id]    VARCHAR (255)  NOT NULL,
    [session_id]      VARCHAR (255)  NOT NULL,
    [trace_id]        VARCHAR (255)  NULL,
    [tool_id]         VARCHAR (255)  NOT NULL,
    [tool_name]       VARCHAR (255)  NOT NULL,
    [tool_input]      NVARCHAR (MAX) NOT NULL,
    [tool_output]     NVARCHAR (MAX) NULL,
    [tool_message]    NVARCHAR (MAX) NULL,
    [status]          VARCHAR (50)   NULL,
    [executing_agent] VARCHAR (255)  NULL,
    [tokens_used]     INT            NULL,
    PRIMARY KEY CLUSTERED ([tool_call_id] ASC)
);


GO

