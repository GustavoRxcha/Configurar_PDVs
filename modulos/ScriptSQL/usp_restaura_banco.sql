-- DECLARAÇÃO DE VARIÁVEIS GLOBAIS
DECLARE @LOJA_NOVA BIT = 1; -- Defina o valor desejado (1 ou 0)
DECLARE @CAIXA NVARCHAR(3) = ?; -- Defina o número do caixa desejado
DECLARE @SAT_ASSINATURA NVARCHAR(4000) = NULL; -- Opcional
DECLARE @ELAPSED_TIME INT;
DECLARE @EMPRESA NVARCHAR(3);
DECLARE @END_TIME DATETIME;
DECLARE @ESTADO NVARCHAR(2);
DECLARE @HOURS VARCHAR(10);
DECLARE @INSCRICAO_FEDERAL NVARCHAR(50);
DECLARE @MAX_ABERTURA BIGINT;
DECLARE @MAX_SANGRIA BIGINT;
DECLARE @MAX_SUPRIMENTO BIGINT;
DECLARE @MINUTES VARCHAR(10);
DECLARE @SECONDS VARCHAR(10);
DECLARE @SRVPRODUCT_BALCAO SYSNAME;
DECLARE @START_TIME DATETIME;
DECLARE @TOTAL_EXECUTION_TIME NVARCHAR(10);
DECLARE @ULTIMO_CUPOM_CNPJ NUMERIC(10);
DECLARE @VERSAO NVARCHAR(50);
DECLARE @temp__CHECKIDENT_RESEED typ_CHECKIDENT_RESEED;
DECLARE @temp__EXISTE_LOJA typ_EXISTE_LOJA;
DECLARE @temp__ULTIMO_CUPOM typ_ULTIMO_CUPOM;
DECLARE @temp__VERSOES typ_VERSOES;

-- DECLARAÇÕES LOCAIS
DECLARE @srvproduct_counter SYSNAME = 'w999alwayson.intra.drogariasnissei.com.br';
DECLARE @server_name SYSNAME;
DECLARE @srvproduct SYSNAME;
DECLARE @catalog SYSNAME;
DECLARE @rmtuser SYSNAME;
DECLARE @rmtpassword SYSNAME;
DECLARE @index_while INT;
DECLARE @central_servidor SYSNAME;
DECLARE @central_banco SYSNAME;
DECLARE @central_usuario SYSNAME;
DECLARE @central_senha SYSNAME;
DECLARE @linkedservernameprefix NVARCHAR(255) = 'linked_server_';
DECLARE @linkedservername NVARCHAR(255);
DECLARE @dropstatement NVARCHAR(MAX);
DECLARE @active BIT;
DECLARE @isup BIT = 0;
DECLARE @test INT;
DECLARE @TABLE_NAME NVARCHAR(255) = NULL;

-- Tabela temporária para servidores vinculados
DECLARE @servers TABLE (
    srv_name NVARCHAR(128),
    srv_providername NVARCHAR(128),
    srv_product NVARCHAR(128),
    srv_datasource NVARCHAR(4000),
    srv_providerstring NVARCHAR(4000),
    srv_location NVARCHAR(4000),
    srv_cat NVARCHAR(128),
    active BIT DEFAULT 1
);

-- INÍCIO DO SCRIPT PRINCIPAL
BEGIN
    -- Obtenção dos dados iniciais
    SELECT @EMPRESA = RIGHT(dbo.DESCOBRE_LOJA_LOCAL(), LEN(dbo.DESCOBRE_LOJA_LOCAL()) - CHARINDEX('_', dbo.DESCOBRE_LOJA_LOCAL()));
    SELECT @SRVPRODUCT_BALCAO = LEFT(dbo.DESCOBRE_LOJA_LOCAL(), CHARINDEX('_', dbo.DESCOBRE_LOJA_LOCAL()) - 1);
    SELECT @START_TIME = GETDATE();

    -- Limpeza de tabelas temporárias, se existirem
    IF OBJECT_ID('tempdb..#temp__PARAMETROS') IS NOT NULL
        DROP TABLE #temp__PARAMETROS;

    -- Criação de tabela temporária para armazenar parâmetros
    SELECT TOP 1
        BAIRRO,
        CEP,
        CIDADE,
        MUNICIPIO_IBGE,
        COMPLEMENTO,
        ENDERECO,
        ESTADO,
        INSCRICAO_ESTADUAL,
        INSCRICAO_FEDERAL,
        NUMERO,
        FPOPULAR_USUARIO,
        TELEFONE
    INTO #temp__PARAMETROS
    FROM PARAMETROS WITH (NOLOCK)
    WHERE 1 = 2;

    -- Verificação da existência da loja
    INSERT INTO @temp__EXISTE_LOJA
    EXEC ('SELECT TOP 1 LOJA, ATIVA FROM LOJAS WITH (NOLOCK) WHERE LOJA = ''' + @EMPRESA + '''') AT [PROCFIT_CONSULTA];

    IF @@ROWCOUNT = 0 OR (SELECT TOP 1 ATIVA FROM @temp__EXISTE_LOJA) != 'S'
    BEGIN
        RAISERROR('A instância selecionada não está associada a uma loja válida ou ativa. Por favor, verifique sua conexão ou valide o cadastro da loja.', 15, -1);
        RETURN;
    END;

    -- Continuação do script...
    INSERT INTO #temp__PARAMETROS
    EXEC ('
        SELECT UPPER(A.BAIRRO) AS BAIRRO, 
               dbo.SO_NUMERO(A.CEP) AS CEP, 
               UPPER(A.CIDADE) AS CIDADE, 
               A.CODIGO_IBGE AS MUNICIPIO_IBGE, 
               ISNULL(A.COMPLEMENTO, '''') AS COMPLEMENTO, 
               UPPER(A.ENDERECO) AS ENDERECO, 
               UPPER(A.ESTADO) AS ESTADO, 
               dbo.SO_NUMERO(B.INSCRICAO_ESTADUAL) AS INSCRICAO_ESTADUAL, 
               dbo.SO_NUMERO(B.INSCRICAO_FEDERAL) AS INSCRICAO_FEDERAL, 
               A.NUMERO AS NUMERO, 
               ISNULL(C.FPOPULAR_USUARIO, '''') AS FPOPULAR_USUARIO, 
               D.NUMERO AS TELEFONE 
        FROM ENDERECOS AS A WITH (NOLOCK) 
        JOIN PESSOAS_JURIDICAS AS B WITH (NOLOCK) ON A.ENTIDADE = B.ENTIDADE 
        OUTER APPLY (SELECT TOP 1 X.FPOPULAR_USUARIO FROM EMPRESAS_USUARIAS AS X WITH (NOLOCK) WHERE X.EMPRESA_USUARIA = B.ENTIDADE) AS C 
        OUTER APPLY (SELECT TOP 1 Y.NUMERO FROM TELEFONES AS Y WITH (NOLOCK) WHERE Y.FORMULARIO_ORIGEM = 21 AND Y.ENTIDADE = B.ENTIDADE) AS D 
        WHERE B.ENTIDADE = ''' + @EMPRESA + '''
    ') AT [PROCFIT_CONSULTA];

    IF @@ROWCOUNT = 0
    BEGIN
        RAISERROR('Não foi encontrado um cadastro correspondente para a loja. Verifique os formulários específicos para pessoas jurídicas e empresas usuárias.', 15, -1);
        RETURN;
    END;

    -- Restante da lógica...
    SELECT TOP 1
        @ESTADO = ESTADO,
        @INSCRICAO_FEDERAL = INSCRICAO_FEDERAL
    FROM #temp__PARAMETROS;

    IF @ESTADO != 'SP'
    BEGIN
        INSERT INTO @temp__ULTIMO_CUPOM
        EXEC ('
            SELECT TOP 1 CAST(ECF_CUPOM AS NUMERIC(10)) + 10 AS ECF_CUPOM 
            FROM PDV_VENDAS AS X WITH (NOLOCK) 
            WHERE X.STATUS = ''A'' 
              AND X.CAIXA = ''' + @CAIXA + ''' 
              AND X.NFCE_CHAVE IS NOT NULL 
              AND SUBSTRING(X.NFCE_CHAVE, 7, 14) = ''' + @INSCRICAO_FEDERAL + ''' 
            ORDER BY ECF_CUPOM DESC
        ') AT [PROCFIT_CONSULTA];

        SELECT TOP 1
            @ULTIMO_CUPOM_CNPJ = ISNULL(ULTIMO_CUPOM_CNPJ, 0)
        FROM @temp__ULTIMO_CUPOM;

        TRUNCATE TABLE NFCE_NUMERACAO_NF;
        INSERT INTO NFCE_NUMERACAO_NF (SERIE, NUMERO)
        SELECT @CAIXA, @ULTIMO_CUPOM_CNPJ;
    END;

    IF @LOJA_NOVA = 1
    BEGIN
        INSERT INTO @temp__VERSOES
        EXEC ('
            SELECT TOP 1 VERSAO 
            FROM PDV_VENDAS WITH (NOLOCK) 
            WHERE LOJA = ''' + @EMPRESA + ''' 
               OR LOJA = (
                   SELECT TOP 1 A.ENTIDADE 
                   FROM ENDERECOS AS A WITH (NOLOCK) 
                   JOIN LOJAS AS B WITH (NOLOCK) ON A.ENTIDADE = B.LOJA AND B.ATIVA = ''S'' 
                   WHERE A.ESTADO = (
                       SELECT TOP 1 ESTADO 
                       FROM ENDERECOS AS X WITH (NOLOCK) 
                       WHERE X.ENTIDADE = ''' + @EMPRESA + ''' 
                         AND X.ENTIDADE != A.ENTIDADE
                   ) 
                   ORDER BY A.ENTIDADE ASC
               ) 
            ORDER BY MOVIMENTO DESC, VERSAO DESC
        ') AT [PROCFIT_CONSULTA];

        SELECT TOP 1
            @VERSAO = VERSAO
        FROM @temp__VERSOES;

        UPDATE A
        SET BAIRRO = B.BAIRRO,
            CAIXA = @CAIXA,
            CEP = B.CEP,
            CIDADE = B.CIDADE,
            COMPLEMENTO = B.COMPLEMENTO,
            DB_SERVIDOR = @SRVPRODUCT_BALCAO,
            ECF_SERIE = @CAIXA,
            EMPRESA = @EMPRESA,
            ENDERECO = B.ENDERECO,
            ESTADO = B.ESTADO,
            INSCRICAO_ESTADUAL = B.INSCRICAO_ESTADUAL,
            INSCRICAO_FEDERAL = B.INSCRICAO_FEDERAL,
            LOJA = @EMPRESA,
            LOJA_SITEF = CASE LEN(@EMPRESA) 
                            WHEN 1 THEN '0000000' + @EMPRESA 
                            WHEN 2 THEN '000000' + @EMPRESA 
                            WHEN 3 THEN '00000' + @EMPRESA 
                         END,
            NFCE_SERIE = @CAIXA,
            NUMERO = B.NUMERO,
            FPOPULAR_USUARIO = B.FPOPULAR_USUARIO,
            TELEFONE = B.TELEFONE,
            TERMINAL_SITEF = '000000' + @CAIXA,
            VERSAO = ISNULL(@VERSAO, '3.0.0.200')
        FROM PARAMETROS AS A WITH (NOLOCK)
        CROSS JOIN #temp__PARAMETROS AS B;

        IF @ESTADO = 'SP'
        BEGIN
            UPDATE A
            SET IMPRESSORA = 'SAT',
                SAT_IMPRESSORA = 'Bematech_MP4200TH_miniprinter',
                SAT_CODIGO_ATIVACAO = '00000000',
                SAT_ASSINATURA = ISNULL(@SAT_ASSINATURA, 'sgr-sat sistema de gestao e retaguarda do sat'),
                SAT_TAMANHO_FONTE = 8,
                SAT_ALTURA_LINHA = 60,
                SAT_DLL = 'libSATDLL_Dual64b.so',
                SAT_AMBIENTE = 1,
                SAT_VERSAO_LAYOUT = 0.07,
                SAT_MARGEM_ESQUERDA = 0,
                SAT_IP = '.\SQLEXPRESS',
                SAT_PORTA = 220,
                SAT_REGIME_TRIBUTARIO = 'N',
                SAT_DIRETO = 'N',
                SAT_DIRETO_MODELO = 2,
                SAT_FONTE = 'Courier New',
                SAT_MARGEM_DIREITA = NULL,
                SAT_LARGURA_BOBINA = 270,
                TEXTO_ECF = 'Troca mediante cupom fiscal até 30 dias, exceto medicamentos de uso controlados e termolábeis.'
            FROM PARAMETROS AS A WITH (NOLOCK);
        END
        ELSE
        BEGIN
            UPDATE TOP (1) A
            SET NFCE_NUMERACAO_INICIAL = @ULTIMO_CUPOM_CNPJ
            FROM PARAMETROS AS A WITH (NOLOCK);

            IF @ESTADO = 'SC'
            BEGIN
                UPDATE A
                SET NFCE_TOKEN = 'AAE86070-7C38-4A85-956A-D643F838B846',
                    NFCE_TOKEN_ID = 1,
                    UF_IBGE = 42,
                    MUNICIPIO_IBGE = ISNULL(B.MUNICIPIO_IBGE, 1),
                    NFCE_DIRETA = 'S'
                FROM PARAMETROS AS A WITH (NOLOCK)
                CROSS JOIN #temp__PARAMETROS AS B;
            END;
        END;
    END
    ELSE
    BEGIN
        -- Remoção de servidores vinculados existentes
        IF EXISTS (SELECT TOP 1 1 FROM sys.servers WHERE name = N'BALCAO')
            EXEC master.dbo.sp_dropserver @server = N'BALCAO', @droplogins = 'droplogins';
        IF EXISTS (SELECT TOP 1 1 FROM sys.servers WHERE name = N'PROCFIT_CONSULTA')
            EXEC master.dbo.sp_dropserver @server = N'PROCFIT_CONSULTA', @droplogins = 'droplogins';
        IF EXISTS (SELECT TOP 1 1 FROM sys.servers WHERE name = N'RETAGUARDA')
            EXEC master.dbo.sp_dropserver @server = N'RETAGUARDA', @droplogins = 'droplogins';

        -- Limpeza de tabelas temporárias, se existirem
        DROP TABLE IF EXISTS #temp_link_server_cx;

        -- Criação de tabela temporária para armazenar os IPs e caixas
        CREATE TABLE #temp_link_server_cx (IP NVARCHAR(70), CAIXA VARCHAR(3));

        -- Inserção dos IPs e caixas na tabela temporária
        INSERT INTO #temp_link_server_cx (IP, CAIXA)
        EXEC ('SELECT TOP 5 B.IP, B.CAIXA FROM LOJAS AS A WITH (NOLOCK) JOIN LOJAS_PDV AS B WITH (NOLOCK) ON A.REGISTRO = B.REGISTRO WHERE A.LOJA = ''' + @EMPRESA + ''' AND B.CAIXA != ''' + @CAIXA + ''' AND LEN(REVERSE(SUBSTRING(REVERSE(B.IP), 1, CHARINDEX(''.'', REVERSE(B.IP)) - 1))) = 1') AT [PROCFIT_CONSULTA];

        -- Verificação de IPs válidos
        IF NOT EXISTS (SELECT TOP 1 1 FROM #temp_link_server_cx)
        BEGIN
            RAISERROR('Nenhum endereço de IP válido foi identificado para a loja conectada. Por favor, verifique as informações de cadastro de lojas e pontos de venda na retaguarda.', 15, -1);
            RETURN;
        END;

        -- Limpeza de tabelas temporárias, se existirem
        DROP TABLE IF EXISTS #temp_addlinkedserver;

        -- Criação de tabela temporária para armazenar os servidores vinculados
        SELECT ROW_NUMBER() OVER (PARTITION BY NULL ORDER BY B.CAIXA ASC) AS id,
               @linkedservernameprefix + B.CAIXA AS server_name,
               B.[IP] AS srvproduct,
               'PDV' AS catalog,
               A.DB_USUARIO AS rmtuser,
               A.DB_SENHA AS rmtpassword
        INTO #temp_addlinkedserver
        FROM PARAMETROS AS A,
             #temp_link_server_cx AS B;

        -- Processamento dos servidores vinculados
        SET @index_while = (SELECT TOP 1 MIN(id) FROM #temp_addlinkedserver);

        WHILE @index_while IS NOT NULL
        BEGIN
            SELECT @server_name = server_name,
                   @srvproduct = srvproduct,
                   @catalog = catalog,
                   @rmtuser = rmtuser,
                   @rmtpassword = rmtpassword
            FROM #temp_addlinkedserver
            WHERE id = @index_while;

            -- Adição do servidor vinculado
            EXEC master.dbo.sp_addlinkedserver
                @server = @server_name,
                @srvproduct = @srvproduct,
                @provider = N'SQLNCLI',
                @datasrc = @srvproduct,
                @catalog = @catalog;

            -- Configuração das credenciais de login
            EXEC master.dbo.sp_addlinkedsrvlogin
                @rmtsrvname = @server_name,
                @useself = N'False',
                @locallogin = NULL,
                @rmtuser = @rmtuser,
                @rmtpassword = @rmtpassword;

            -- Configuração das opções do servidor vinculado
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'collation compatible', @optvalue = N'false';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'data access', @optvalue = N'true';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'dist', @optvalue = N'false';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'pub', @optvalue = N'false';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'rpc', @optvalue = N'true';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'rpc out', @optvalue = N'true';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'sub', @optvalue = N'false';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'connect timeout', @optvalue = N'0';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'collation name', @optvalue = NULL;
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'lazy schema validation', @optvalue = N'false';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'query timeout', @optvalue = N'0';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'use remote collation', @optvalue = N'true';
            EXEC master.dbo.sp_serveroption @server = @server_name, @optname = N'remote proc transaction promotion', @optvalue = N'false';

            -- Avanço para o próximo servidor vinculado
            SET @index_while = (SELECT TOP 1 MIN(id) FROM #temp_addlinkedserver WHERE id > @index_while);
        END;

        -- Teste dos servidores vinculados
        INSERT INTO @servers (srv_name, srv_providername, srv_product, srv_datasource, srv_providerstring, srv_location, srv_cat)
        EXEC sys.sp_linkedservers;

        DECLARE servercursor CURSOR FOR
        SELECT srv_name, active
        FROM @servers
        WHERE srv_cat = N'PDV'
        ORDER BY srv_name ASC;

        OPEN servercursor;
        FETCH NEXT FROM servercursor INTO @linkedservername, @active;

        WHILE @@FETCH_STATUS = 0
        BEGIN
            BEGIN TRY
                EXEC @test = sp_testlinkedserver @linkedservername;
                IF @test = 0
                    SET @isup = 1;
                ELSE
                    SET @isup = 0;
            END TRY
            BEGIN CATCH
                SET @isup = 0;
            END CATCH;

            IF @active != @isup
            BEGIN
                UPDATE A
                SET Active = @isup
                FROM @servers AS A
                WHERE srv_name = @linkedservername;
            END;

            FETCH NEXT FROM servercursor INTO @linkedservername, @active;
        END;

        CLOSE servercursor;
        DEALLOCATE servercursor;

        -- Limpeza de tabelas temporárias, se existirem
        DROP TABLE IF EXISTS #temp_drop_servers;

        -- Criação de tabela temporária para armazenar os servidores a serem removidos
        SELECT ROW_NUMBER() OVER (PARTITION BY srv_cat ORDER BY srv_name ASC) AS row_id,
               ROW_NUMBER() OVER (PARTITION BY NULL ORDER BY srv_name ASC) AS id,
               *
        INTO #temp_drop_servers
        FROM @servers;

        -- Renomeação do servidor vinculado principal
        SELECT @LinkedServerName = srv_name
        FROM #temp_drop_servers
        WHERE srv_name LIKE 'linked_server_%'
          AND row_id = 1;

        EXEC master.dbo.sp_serveroption @server = @LinkedServerName, @optname = N'name', @optvalue = N'PDV_CONSULTA';

        -- Remoção dos servidores vinculados desnecessários
        DELETE FROM #temp_drop_servers
        WHERE srv_name IN (N'BALCAO', N'PROCFIT_CONSULTA', N'RETAGUARDA', @LinkedServerName);

        SET @index_while = (SELECT TOP 1 MIN(id) FROM #temp_drop_servers);

        WHILE @index_while IS NOT NULL
        BEGIN
            SELECT @linkedservername = srv_name FROM #temp_drop_servers WHERE ID = @index_while;

            EXEC master.dbo.sp_dropserver @server = @linkedservername, @droplogins = 'droplogins';

            SET @index_while = (SELECT TOP 1 MIN(id) FROM #temp_drop_servers WHERE id > @index_while);
        END;

        -- Transação para recriar a tabela de parâmetros
        BEGIN TRY
            BEGIN TRANSACTION;

            IF EXISTS (SELECT TOP 1 2 FROM sys.objects WHERE name = N'PARAMETROS')
                DROP TABLE PARAMETROS;

            IF EXISTS (SELECT TOP 1 2 FROM sys.servers WHERE name = N'PDV_CONSULTA')
            BEGIN
                EXEC ('
                    SELECT TOP 1 * 
                    INTO PARAMETROS 
                    FROM [PDV_CONSULTA].[PDV].dbo.PARAMETROS
                ');
            END
            ELSE
            BEGIN
                ROLLBACK TRANSACTION;
                RAISERROR('O servidor vinculado [PDV_CONSULTA] não foi encontrado, resultando no cancelamento da consulta. Por favor, verifique a configuração do servidor e tente novamente.', 15, -1);
                RETURN;
            END;

            UPDATE TOP (1) A
            SET CAIXA = @CAIXA,
                DB_SERVIDOR = @SRVPRODUCT_BALCAO,
                ECF_SERIE = @CAIXA,
                NFCE_NUMERACAO_INICIAL = @ULTIMO_CUPOM_CNPJ,
                NFCE_SERIE = @CAIXA,
                TERMINAL_SITEF = '000000' + @CAIXA
            FROM PARAMETROS AS A WITH (NOLOCK);

            COMMIT TRANSACTION;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0
                ROLLBACK TRANSACTION;
            RAISERROR('Erro durante a transação de recriação da tabela de parâmetros. Tente novamente.', 15, -1);
            RETURN;
        END CATCH;

        -- Reseed das tabelas específicas
        BEGIN TRY
            BEGIN TRANSACTION;

            INSERT INTO @temp__CHECKIDENT_RESEED
            EXEC ('
                SELECT 1, ISNULL(MAX(ABERTURA), 0) + 10 FROM PDV_CAIXAS WITH (NOLOCK) WHERE LOJA = ''' + @EMPRESA + ''' AND CAIXA = ''' + @CAIXA + ''' 
                UNION 
                SELECT 2, ISNULL(MAX(SANGRIA), 0) + 10 FROM PDV_SANGRIAS WITH (NOLOCK) WHERE LOJA = ''' + @EMPRESA + ''' AND CAIXA = ''' + @CAIXA + ''' 
                UNION 
                SELECT 3, ISNULL(MAX(SUPRIMENTO), 0) + 10 FROM PDV_SUPRIMENTOS WITH (NOLOCK) WHERE LOJA = ''' + @EMPRESA + ''' AND CAIXA = ''' + @CAIXA + '''
            ') AT [PROCFIT_CONSULTA];

            SELECT TOP 1 @MAX_ABERTURA = CL_RESEED FROM @temp__CHECKIDENT_RESEED WHERE ID = 1;
            SELECT TOP 1 @MAX_SANGRIA = CL_RESEED FROM @temp__CHECKIDENT_RESEED WHERE ID = 2;
            SELECT TOP 1 @MAX_SUPRIMENTO = CL_RESEED FROM @temp__CHECKIDENT_RESEED WHERE ID = 3;

            DBCC CHECKIDENT('[CAIXAS]', RESEED, @MAX_ABERTURA) WITH NO_INFOMSGS;
            DBCC CHECKIDENT('[SANGRIAS]', RESEED, @MAX_SANGRIA) WITH NO_INFOMSGS;
            DBCC CHECKIDENT('[SUPRIMENTOS]', RESEED, @MAX_SUPRIMENTO) WITH NO_INFOMSGS;

            COMMIT TRANSACTION;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0
                ROLLBACK TRANSACTION;
            PRINT CHAR(13) + 'A tentativa de reseed nas tabelas específicas falhou. Recomenda-se uma revisão no processo de reinicialização da chave dos objetos.';
        END CATCH;
    END;

    -- Truncagem e preenchimento da tabela VEZES
    TRUNCATE TABLE VEZES;

    INSERT INTO VEZES (SEQUENCIA)
    SELECT TOP 80000
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS SEQUENCIA
    FROM master.sys.all_objects AS A
    CROSS JOIN master.sys.all_objects AS B;

    -- Sincronização de tabelas
    SET @index_while = (SELECT TOP 1 MIN(ID) FROM TABELA_SYNC_BALCAO);

    WHILE @index_while IS NOT NULL
    BEGIN
        SELECT TOP 1
            @TABLE_NAME = TABELA
        FROM TABELA_SYNC_BALCAO
        WHERE ID = @index_while;

        BEGIN TRY
            EXEC ('
                TRUNCATE TABLE ' + @TABLE_NAME + ';
                INSERT INTO ' + @TABLE_NAME + ' 
                SELECT TOP 1 * 
                FROM [BALCAO].[LOJA].[dbo].[' + @TABLE_NAME + '];
            ');
        END TRY
        BEGIN CATCH
            EXEC ('
                DECLARE @SQL NVARCHAR(MAX);
                DROP TABLE IF EXISTS #' + @TABLE_NAME + ';
                SELECT TOP 1 * 
                INTO #' + @TABLE_NAME + ' 
                FROM [BALCAO].[LOJA].[dbo].[' + @TABLE_NAME + '] 
                WHERE 1 = 2;
                IF EXISTS (SELECT TOP 1 1 FROM sys.objects WHERE object_id = OBJECT_ID(N''[dbo].[' + @TABLE_NAME + ']'') AND type IN (N''U''))
                    DROP TABLE [dbo].[' + @TABLE_NAME + '];
                SELECT @SQL = dbo.FN_TABLE_STRUCTURE(''SELECT * FROM #' + @TABLE_NAME + ''', ''' + @TABLE_NAME + ''');
                EXEC (@SQL);
            ');
        END CATCH;

        SET @index_while = (SELECT TOP 1 MIN(ID) FROM TABELA_SYNC_BALCAO WHERE ID > @index_while);
    END;

    -- Finalização do script
    SET @END_TIME = GETDATE();
    SET @ELAPSED_TIME = DATEDIFF(SECOND, @START_TIME, @END_TIME);
    SET @HOURS = CAST(@ELAPSED_TIME / 3600 AS VARCHAR(255));
    SET @MINUTES = CAST((@ELAPSED_TIME % 3600) / 60 AS VARCHAR(255));
    SET @SECONDS = CAST(@ELAPSED_TIME % 60 AS VARCHAR(255));

    IF LEN(@HOURS) = 1 SET @HOURS = '0' + @HOURS;
    IF LEN(@MINUTES) = 1 SET @MINUTES = '0' + @MINUTES;
    IF LEN(@SECONDS) = 1 SET @SECONDS = '0' + @SECONDS;

    SET @TOTAL_EXECUTION_TIME = @HOURS + ':' + @MINUTES + ':' + @SECONDS;

    INSERT INTO RESTAURA_BANCO_PDV_LOG
        (spid, caixa, client_net_address, [host_name], [original_login], [suser_name], total_execution_time)
    SELECT @@SPID, @CAIXA, client_net_address, HOST_NAME(), UPPER(ORIGINAL_LOGIN()), UPPER(SUSER_SNAME()), @TOTAL_EXECUTION_TIME
    FROM sys.dm_exec_connections
    WHERE session_id = @@SPID;

    SELECT EMPRESA, LOJA, LOJA_SITEF, ECF_SERIE, NFCE_SERIE, TERMINAL_SITEF, CAIXA, DB_SERVIDOR, ENDERECO, NUMERO, BAIRRO, CIDADE, CEP, TELEFONE, ESTADO, VERSAO
    FROM PARAMETROS WITH (NOLOCK);
END;