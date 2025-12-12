CREATE TABLE [dbo].[agent_traces] (
    [trace_step_id]         VARCHAR (255)  NOT NULL,
    [session_id]            VARCHAR (255)  NOT NULL,
    [trace_id]              VARCHAR (255)  NOT NULL,
    [user_id]               VARCHAR (255)  NOT NULL,
    [from_agent]            VARCHAR (255)  NULL,
    [current_agent]         VARCHAR (255)  NULL,
    [step_order]            INT            DEFAULT ((1)) NULL,
    [execution_duration_ms] INT            NULL,
    [success]               BIT            DEFAULT ((1)) NULL,
    [error_message]         NVARCHAR (MAX) NULL,
    PRIMARY KEY CLUSTERED ([trace_step_id] ASC)
);


GO

