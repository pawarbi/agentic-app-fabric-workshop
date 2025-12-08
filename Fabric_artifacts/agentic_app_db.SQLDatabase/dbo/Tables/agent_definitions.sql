CREATE TABLE [dbo].[agent_definitions] (
    [agent_id]        VARCHAR (255)  NOT NULL,
    [name]            VARCHAR (255)  NOT NULL,
    [description]     NVARCHAR (MAX) NULL,
    [llm_config]      NVARCHAR (MAX) NOT NULL,
    [prompt_template] NVARCHAR (MAX) NOT NULL,
    [agent_type]      VARCHAR (100)  DEFAULT ('specialist') NULL,
    [created_at]      DATETIME2 (7)  DEFAULT (getdate()) NULL,
    PRIMARY KEY CLUSTERED ([agent_id] ASC),
    UNIQUE NONCLUSTERED ([name] ASC)
);


GO

