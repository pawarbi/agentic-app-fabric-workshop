CREATE TABLE [dbo].[ai_widgets] (
    [id]                VARCHAR (255)  NOT NULL,
    [user_id]           VARCHAR (255)  NOT NULL,
    [title]             VARCHAR (500)  NOT NULL,
    [description]       VARCHAR (MAX)  NULL,
    [widget_type]       VARCHAR (50)   NOT NULL,
    [config]            NVARCHAR (MAX) NOT NULL,
    [code]              VARCHAR (MAX)  NULL,
    [data_mode]         VARCHAR (20)   NOT NULL,
    [query_config]      NVARCHAR (MAX) NULL,
    [last_refreshed]    DATETIME       NULL,
    [simulation_config] NVARCHAR (MAX) NULL,
    [created_at]        DATETIME       NULL,
    [updated_at]        DATETIME       NULL,
    PRIMARY KEY CLUSTERED ([id] ASC)
);


GO

CREATE NONCLUSTERED INDEX [ix_ai_widgets_user_id]
    ON [dbo].[ai_widgets]([user_id] ASC);


GO

