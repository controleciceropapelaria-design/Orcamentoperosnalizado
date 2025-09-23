# orcamento_pro/ui_components.py
"""
Módulo para componentes de UI reutilizáveis do Streamlit.
Agora com validação de formulários e busca de CEP por API.
"""
import streamlit as st
import pandas as pd
import storage
import config
import re
import requests
import json # <-- Importamos a nova biblioteca

# ================== CONSTANTES E FUNÇÕES AUXILIARES ==================

UFS_BRASIL = ["", "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"]

def is_valid_email(email):
    """Verifica se um email tem um formato básico válido."""
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email)

def format_cep(cep):
    """Formata um CEP para XXXXX-XXX, aceitando apenas dígitos."""
    cep_digits = re.sub(r'\D', '', cep)
    if len(cep_digits) == 8:
        return f"{cep_digits[:5]}-{cep_digits[5:]}"
    return cep # Retorna o original se não tiver 8 dígitos

def format_cnpj(cnpj):
    """Formata um CNPJ para XX.XXX.XXX/XXXX-XX, aceitando apenas dígitos."""
    cnpj_digits = re.sub(r'\D', '', cnpj)
    if len(cnpj_digits) == 14:
        return f"{cnpj_digits[:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:]}"
    return cnpj

def format_telefone(telefone):
    """Formata um telefone para (XX) XXXXX-XXXX, aceitando apenas dígitos."""
    tel_digits = re.sub(r'\D', '', telefone)
    if len(tel_digits) == 11:
        return f"({tel_digits[:2]}) {tel_digits[2:7]}-{tel_digits[7:]}"
    if len(tel_digits) == 10:
        return f"({tel_digits[:2]}) {tel_digits[2:6]}-{tel_digits[6:]}"
    return telefone

def get_address_from_cep(cep):
    """Busca o endereço correspondente a um CEP usando a API ViaCEP."""
    cep_digits = re.sub(r'\D', '', cep)
    if len(cep_digits) != 8:
        return None, "CEP inválido. Deve conter 8 dígitos."
    
    try:
        response = requests.get(f"https://viacep.com.br/ws/{cep_digits}/json/")
        response.raise_for_status() # Lança um erro para status HTTP ruins (4xx ou 5xx)
        data = response.json()
        if data.get("erro"):
            return None, "CEP não encontrado."
        
        return data, None # Retorna os dados do endereço e nenhuma mensagem de erro
    except requests.exceptions.RequestException as e:
        return None, f"Erro de conexão: {e}"

# ================== COMPONENTES DE UI ==================

# ... (as funções display_login_form, display_registration_form, etc., continuam aqui) ...
def display_login_form():
    """Renderiza o formulário de login na barra lateral."""
    st.sidebar.title("🔐 Login")
    with st.sidebar.form("login_form"):
        username = st.text_input("Usuário")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        return submitted, username, password

def display_registration_form():
    """Renderiza o formulário de cadastro de usuário."""
    st.title("📝 Cadastro de Novo Usuário")
    with st.form("registration_form"):
        new_user = st.text_input("Novo Usuário")
        new_pass = st.text_input("Nova Senha", type="password")
        full_name = st.text_input("Nome Completo")
        submitted = st.form_submit_button("Cadastrar")
        return submitted, new_user, new_pass, full_name

def display_sidebar_logged_in():
    """Renderiza a barra lateral para um usuário logado."""
    # Esta função não precisa mais existir aqui, pois a lógica foi movida para app.py
    pass

# orcamento_pro/ui_components.py

def display_client_registration_form():
    """Renderiza o formulário e a tabela de cadastro de clientes com validação e busca de CEP."""
    st.title("📋 Cadastro de Clientes")

    # Inicializa o estado da sessão para os campos de endereço se não existirem
    if 'cep_data' not in st.session_state:
        st.session_state.cep_data = {}

    st.subheader("1. Buscar Endereço (Opcional)")
    col1, col2 = st.columns([1, 2])
    cep_input = col1.text_input("Digite o CEP")
    
    # MUDANÇA AQUI: O botão de busca agora está FORA do st.form
    if col2.button("Buscar Endereço"):
        address_data, error_message = get_address_from_cep(cep_input)
        if error_message:
            st.warning(error_message)
            st.session_state.cep_data = {}
        else:
            st.session_state.cep_data = address_data
            st.success("Endereço encontrado! Os campos abaixo foram preenchidos.")
    
    st.divider()

    # MUDANÇA AQUI: O st.form começa DEPOIS da lógica do CEP
    with st.form("cadastro_cliente"):
        st.subheader("2. Preencher Dados do Cliente")

        # Campos de endereço usam os valores do session_state
        cep_data = st.session_state.cep_data

        col1, col2 = st.columns(2)
        nome = col1.text_input("Nome*")
        razao_social = col2.text_input("Razão Social")
        cnpj = col1.text_input("CNPJ")
        # Use exatamente o nome da coluna do CSV, sem acento e sem espaço extra
        inscricao_estadual = col2.text_input("Inscricao Estadual")  # <-- deve ser igual ao config.COLUNAS_CLIENTES

        email = col1.text_input("Email*")
        telefone = col2.text_input("Telefone")
        
        contato = st.text_input("Nome do Contato")

        # Os campos de endereço agora são preenchidos com base na busca anterior
        endereco = st.text_input("Endereço", value=cep_data.get("logradouro", ""))
        
        col1, col2 = st.columns([2,1])
        cidade = col1.text_input("Cidade", value=cep_data.get("localidade", ""))
        
        uf_index = 0
        if cep_data.get("uf") in UFS_BRASIL:
            uf_index = UFS_BRASIL.index(cep_data.get("uf"))
        uf = col2.selectbox("UF", UFS_BRASIL, index=uf_index)
        
        forma_pagamento = st.text_input("Forma de Pagamento")

        # Este é o único botão permitido dentro de um formulário
        submitted = st.form_submit_button("Cadastrar Cliente")
        if submitted:
            if not nome or not email:
                st.error("Os campos 'Nome' e 'Email' são obrigatórios.")
            elif not is_valid_email(email):
                st.error("Formato de email inválido.")
            else:
                # Garante que o dicionário tem as chaves exatamente como em config.COLUNAS_CLIENTES
                client_data = {
                    "Nome": nome,
                    "Razao Social": razao_social,
                    "CNPJ": format_cnpj(cnpj),
                    "Endereco": endereco,
                    "CEP": format_cep(cep_input),
                    "Cidade": cidade,
                    "UF": uf,
                    "Inscricao Estadual": inscricao_estadual,  # <-- igual ao config.COLUNAS_CLIENTES
                    "Email": email,
                    "Telefone": format_telefone(telefone),
                    "Forma de Pagamento": forma_pagamento,
                    "Contato": contato,
                    "Status": "Ativo"
                }
                # Garante que as colunas estejam na ordem e nomes corretos
                new_client_df = pd.DataFrame([client_data])[config.COLUNAS_CLIENTES]
                st.session_state.df_clientes = pd.concat([st.session_state.df_clientes, new_client_df], ignore_index=True)[config.COLUNAS_CLIENTES]
                storage.save_csv(st.session_state.df_clientes, config.CLIENTES_FILE)
                storage.save_clientes_to_github(st.session_state.df_clientes, st.secrets["github_token"])
                st.success(f"Cliente '{nome}' cadastrado com sucesso!")
                st.session_state.cep_data = {} # Limpa o cache do CEP

    st.divider()
    st.write("### Clientes Cadastrados")
    # CORREÇÃO: converte colunas object para número ou string
    df_clientes = st.session_state.df_clientes.copy()
    for col in df_clientes.columns:
        if df_clientes[col].dtype == "object":
            try:
                df_clientes[col] = pd.to_numeric(df_clientes[col], errors="raise")
            except Exception:
                df_clientes[col] = df_clientes[col].astype(str)
    st.dataframe(df_clientes, width='stretch')

def display_history_page():
    st.title("📜 Meu Histórico de Orçamentos")
    import os
    from generate_ordem_prototipo import generate_ordem_prototipo_pdf
    from datetime import datetime

    user_history = st.session_state.df_orcamentos[
        st.session_state.df_orcamentos["Usuario"] == st.session_state.username
    ].copy()

    # Garante que a coluna existe e preenche NaN com "Pendente"
    if "StatusOrcamento" not in user_history.columns:
        user_history["StatusOrcamento"] = "Pendente"
    user_history["StatusOrcamento"] = user_history["StatusOrcamento"].fillna("Pendente")

    if not user_history.empty:
        st.write("### Orçamentos Criados por Você")
        df_display = user_history[[
            "NomeOrcamentista", "Cliente", "Quantidade", "Produto", "Data", "PropostaPDF", "StatusOrcamento"
        ]].copy()
        df_display.rename(columns={
            "NomeOrcamentista": "Orçamentista",
            "Cliente": "Cliente",
            "Quantidade": "Qtd.",
            "Produto": "Produto",
            "Data": "Data",
            "PropostaPDF": "Proposta PDF",
            "StatusOrcamento": "Status"
        }, inplace=True)
        # CORREÇÃO: converte colunas object para número ou string
        for col in df_display.columns:
            try:
                df_display[col] = pd.to_numeric(df_display[col])
            except Exception:
                df_display[col] = df_display[col].astype(str)
        st.dataframe(df_display, width='stretch', hide_index=True)

        # NOVA SEÇÃO: Seleção de versão para editar ou baixar proposta
        st.write("### Selecionar Versão do Orçamento")
        selected_idx = st.selectbox(
            "Escolha o orçamento:",
            options=list(user_history.index),
            format_func=lambda i: f"{user_history.loc[i, 'Produto']} - {user_history.loc[i, 'Cliente']} ({user_history.loc[i, 'Data']})"
        )
        versoes_json = user_history.loc[selected_idx].get("VersoesJSON", "[]")
        try:
            versoes = json.loads(versoes_json)
        except Exception:
            versoes = []
        versoes = versoes if isinstance(versoes, list) else []
        versoes.append({"timestamp": user_history.loc[selected_idx].get("Data", ""), "data": user_history.loc[selected_idx].to_dict()})
        versao_labels = [f"Versão {i+1} - {v['timestamp']}" for i, v in enumerate(versoes)]
        versao_idx = st.selectbox(
            "Escolha a versão:",
            options=list(range(len(versoes))),
            format_func=lambda i: versao_labels[i]
        )
        col_download = st.columns(1)[0]
        if col_download.button("Baixar Proposta PDF desta versão"):
            pdf_path = versoes[versao_idx]["data"].get("PropostaPDF", "")
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as fpdf:
                    st.download_button("Baixar Proposta PDF", fpdf, file_name=os.path.basename(pdf_path))
            else:
                st.warning("Arquivo PDF não encontrado para esta versão.")

        # Expander de detalhes e botões de ação por orçamento
        with st.expander("Ver Todos os Detalhes e Ajustes de um Orçamento"):
            id_orcamento = user_history.loc[selected_idx, 'ID']
            orcamento_selecionado = user_history[user_history['ID'] == id_orcamento].iloc[0]
            st.write(f"**Detalhes Completos do Orçamento {id_orcamento}:**")
            # CORREÇÃO: converte colunas object para número ou string
            df_detalhes = orcamento_selecionado.drop('AjustesJSON').to_frame().T.copy()
            for col in df_detalhes.columns:
                if df_detalhes[col].dtype == "object":
                    try:
                        df_detalhes[col] = pd.to_numeric(df_detalhes[col], errors="raise")
                    except Exception:
                        df_detalhes[col] = df_detalhes[col].astype(str)
            st.dataframe(df_detalhes)
            
            # Mostra status colorido no topo do expander
            status = orcamento_selecionado.get('StatusOrcamento', 'Pendente')
            if pd.isna(status):
                status = "Pendente"
            status = str(status).strip().capitalize()
            # Mostra status simples sem cor customizada
            st.markdown(f"<span style='font-weight:bold;font-size:1.1em;'>Status: {status}</span>", unsafe_allow_html=True)

            # Botão para baixar o PDF da proposta, se existir
            pdf_path = orcamento_selecionado.get("PropostaPDF", "")
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as fpdf:
                    st.download_button("Baixar Proposta PDF", fpdf, file_name=os.path.basename(pdf_path), key=f"download_pdf_{id_orcamento}")

            # Regras de exibição dos botões
            # Pendente: Baixar, Editar, Excluir, Aprovar
            # Aprovado: Baixar, Editar, Suspender, Finalizar, Gerar Ordem
            # Suspenso: Baixar, Editar, Excluir, Aprovar, Finalizar, Gerar Ordem
            # Finalizado: Baixar, Editar, Gerar Ordem

            btns = []
            if status == "Pendente":
                btns = ["editar", "excluir", "aprovar"]
            elif status == "Aprovado":
                btns = ["editar", "suspender", "finalizar", "ordem"]
            elif status == "Suspenso":
                btns = ["editar", "excluir", "aprovar", "finalizar", "ordem"]
            elif status == "Finalizado":
                btns = ["editar", "ordem"]

            cols = st.columns(len(btns)) if btns else []

            # ...estilos customizados removidos para restaurar o padrão dos botões...

            col_idx = 0
            for idx, btn in enumerate(btns):
                with cols[idx]:
                    if btn == "editar":
                        if st.button("Editar esta versão", key=f"editar_{id_orcamento}_details"):
                            selecoes = json.loads(versoes[versao_idx]["data"].get("SelecoesJSON", "{}"))
                            for key, value in selecoes.items():
                                st.session_state[key] = value
                            st.session_state['selected_client'] = versoes[versao_idx]["data"].get('Cliente', '')
                            try:
                                st.session_state['budget_quantity'] = int(versoes[versao_idx]["data"].get('Quantidade', 15000))
                            except Exception:
                                st.session_state['budget_quantity'] = 15000
                            st.session_state['sel_produto'] = versoes[versao_idx]["data"].get('Produto', '')
                            for extra_key in [
                                'selected_laminacao', 'selected_hot_stamping', 'selected_silk',
                                'sel_capa_papel', 'sel_capa_impressao', 'sel_capa_couro', 'sel_produto'
                            ]:
                                if extra_key in selecoes:
                                    st.session_state[extra_key] = selecoes[extra_key]
                            st.session_state['ajustes'] = json.loads(versoes[versao_idx]["data"].get('AjustesJSON', '[]'))
                            st.session_state['editing_id'] = versoes[versao_idx]["data"].get('ID', '')
                            st.session_state['edit_loaded'] = True
                            st.session_state['page'] = "Orçamento"
                            st.success(f"Versão {versao_idx+1} carregada para edição!")
                            st.rerun()
                        st.markdown(f"""
                        <style>
                        div[data-testid='stButton'] button#editar_{id_orcamento}_details {{
                            background-color: #1976d2 !important;
                            color: #fff !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    elif btn == "excluir":
                        if st.button("Excluir Orçamento", key=f"excluir_{id_orcamento}_details"):
                            idx_del = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento].index[0]
                            st.session_state.df_orcamentos = st.session_state.df_orcamentos.drop(idx_del).reset_index(drop=True)
                            storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                            storage.delete_orcamento_from_github(st.secrets["github_token"])
                            st.success(f"Orçamento {id_orcamento} excluído com sucesso!")
                            st.rerun()
                        st.markdown(f"""
                        <style>
                        div[data-testid='stButton'] button#excluir_{id_orcamento}_details {{
                            background-color: #f44336 !important;
                            color: #fff !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    elif btn == "aprovar":
                        if st.button("Aprovar Orçamento", key=f"aprovar_{id_orcamento}_details"):
                            idx_apr = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento].index[0]
                            st.session_state.df_orcamentos.loc[idx_apr, "StatusOrcamento"] = "Aprovado"
                            storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                            storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                            st.success(f"Orçamento {id_orcamento} aprovado!")
                            st.rerun()
                        # ...estilo customizado removido: botão aprovar...
                    elif btn == "suspender":
                        if st.button("Suspender Orçamento", key=f"suspender_{id_orcamento}_details"):
                            idx_sus = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento].index[0]
                            st.session_state.df_orcamentos.loc[idx_sus, "StatusOrcamento"] = "Suspenso"
                            storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                            storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                            st.success(f"Orçamento {id_orcamento} suspenso!")
                            st.rerun()
                        st.markdown(f"""
                        <style>
                        div[data-testid='stButton'] button#suspender_{id_orcamento}_details {{
                            background-color: #ffeb3b !important;
                            color: #222 !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    elif btn == "finalizar":
                        if st.button("Finalizar Orçamento", key=f"finalizar_{id_orcamento}_details"):
                            idx_fin = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento].index[0]
                            st.session_state.df_orcamentos.loc[idx_fin, "StatusOrcamento"] = "Finalizado"
                            storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                            storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                            st.success(f"Orçamento {id_orcamento} finalizado!")
                            st.rerun()
                        st.markdown(f"""
                        <style>
                        div[data-testid='stButton'] button#finalizar_{id_orcamento}_details {{
                            background-color: #e74c3c !important;
                            color: #fff !important;
                        }}
                        </style>
                        """, unsafe_allow_html=True)
                    elif btn == "ordem":
                        custom_btn_style = f"""
                        <style>
                        div[data-testid="stButton"] button#gerar_ordem_prototipo_{id_orcamento} {{
                            background-color: #fff !important;
                            color: #222 !important;
                            border: 1px solid #ccc !important;
                        }}
                        </style>
                        """
                        st.markdown(custom_btn_style, unsafe_allow_html=True)
                        if st.button("Gerar Ordem de Protótipo", key=f"gerar_ordem_prototipo_{id_orcamento}"):
                            from generate_ordem_prototipo import generate_ordem_prototipo_pdf
                            import os
                            from datetime import datetime
                            proposta_data = {
                                "data": datetime.now().strftime("%d/%m/%Y"),
                                "cliente": orcamento_selecionado.get("Cliente", ""),
                                "responsavel": "",
                                "numero_orcamento": orcamento_selecionado.get("ID", ""),
                                "versao_orcamento": orcamento_selecionado.get("VersoesOrcamento", 1),
                                "produto": orcamento_selecionado.get("Produto", ""),
                                "quantidade": 2,
                                "descrição": orcamento_selecionado.get("descrição", ""),
                                "Unitario": orcamento_selecionado.get("PrecoVenda", ""),
                                "total": "",
                                "atendente": orcamento_selecionado.get("NomeOrcamentista", ""),
                                "validade": "",
                                "prazo_de_entrega": "",
                            }
                            try:
                                cliente_row = st.session_state.df_clientes[
                                    st.session_state.df_clientes["Nome"] == orcamento_selecionado.get("Cliente", "")
                                ]
                                if not cliente_row.empty:
                                    proposta_data["responsavel"] = cliente_row["Contato"].values[0]
                            except Exception:
                                pass
                            propostas_dir = "Propostas"
                            if not os.path.exists(propostas_dir):
                                os.makedirs(propostas_dir, exist_ok=True)
                            ordem_path = os.path.join(
                                propostas_dir,
                                f"OrdemPrototipo_{proposta_data['cliente']}_{proposta_data['produto']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            )
                            generate_ordem_prototipo_pdf(proposta_data, ordem_path)
                            if os.path.exists(ordem_path):
                                with open(ordem_path, "rb") as fpdf:
                                    st.download_button(
                                        "Baixar Ordem de Protótipo PDF",
                                        fpdf,
                                        file_name=os.path.basename(ordem_path),
                                        key=f"download_ordem_{id_orcamento}"
                                    )
                col_idx += 1
            # ...existing code for ajustes_json, ajustes_lista, etc...
    else:
        st.info("Nenhum orçamento encontrado para o seu usuário.")

# ...existing code...

def render_component_selector(component_type: str, df_items: pd.DataFrame, paper_options: list) -> dict:
    """
    Renderiza um seletor genérico para componentes.
    A seção 'Personalizado' agora inicia os campos numéricos com 0.00.
    """
    st.markdown(f"#### {component_type}")
    item_col_name = df_items.columns[0]
    item_list = sorted(df_items[item_col_name].dropna().unique())
    options = ["Nenhum", "Personalizado"] + item_list

    selected_item = st.selectbox(f"Selecione o {component_type}:", options, key=f"sel_{component_type.lower()}")

    result = {"selection": selected_item}
    if selected_item == "Personalizado":
        st.write("Detalhes do Custo Personalizado:")
        col1, col2 = st.columns(2)
        
        result["paper"] = col1.selectbox(
            f"Matéria Prima Principal", paper_options, key=f"paper_{component_type.lower()}"
        )
        # --- MUDANÇA AQUI ---
        result["total_material_cost"] = col1.number_input(
            f"Custo TOTAL da Matéria Prima (R$)", 
            min_value=0.0, 
            value=0.0,  # Inicia com 0.0
            format="%.2f", # Formata para 2 casas decimais
            key=f"mat_cost_{component_type.lower()}"
        )
        # --- MUDANÇA AQUI ---
        result["total_service_cost"] = col2.number_input(
            f"Custo TOTAL do Serviço (R$)", 
            min_value=0.0, 
            value=0.0,  # Inicia com 0.0
            format="%.2f", # Formata para 2 casas decimais
            key=f"serv_cost_{component_type.lower()}"
        )
        
    return result

def render_direct_purchase_selector(category: str, items: list, wireo_map: dict) -> dict:
    """
    Renderiza um seletor genérico para itens de compra direta.
    Retorna um dicionário com o custo calculado e detalhes.
    """
    st.markdown(f"##### {category}")
    item_names = [item['NomeLimpo'] for item in items]
    options = ["Nenhum", "Personalizado"] + sorted(item_names)

    selected_item = st.selectbox(f"Selecione:", options, key=f"cd_{category}", label_visibility="collapsed")

    cost_info = {"cost": 0.0, "details": "Nenhum", "util": 1.0}

    if selected_item == "Personalizado":
        val_unit = st.number_input(f"Valor unitário pers.", min_value=0.0, value=1.0, key=f"vu_{category}", step=0.1)
        util = st.number_input(f"Aproveitamento", min_value=0.01, value=1.0, step=0.01, key=f"util_cd_{category}")
        cost_info["cost"] = val_unit * util
        cost_info["details"] = f"Personalizado (R$ {val_unit:.2f} * {util}) = R$ {cost_info['cost']:.4f}"
        cost_info["util"] = util

    elif selected_item != "Nenhum":
        item_data = next((i for i in items if i['NomeLimpo'] == selected_item), None)
        if item_data:
            price = item_data['VALOR_UNITARIO']
            last_nf = item_data['ULTIMA_NF']

            if category == "WIRE-O":
                qty_box = wireo_map.get(selected_item, 6000)
                rings = st.number_input(f"Nº de anéis por unidade", min_value=1, value=30, step=1, key=f"rings_{selected_item}")
                cost_info["cost"] = (price / qty_box) * rings if qty_box > 0 else 0
                cost_info["util"] = rings # Para wire-o, util representa o nº de anéis
            else:
                util = st.number_input(f"Aproveitamento ({selected_item})", min_value=0.01, value=1.0, step=0.01, key=f"util_{selected_item}")
                cost_info["cost"] = price * util
                cost_info["util"] = util

            cost_info["details"] = f"{selected_item} (NF: {last_nf})"

    return cost_info

def display_admin_panel():
    """Renderiza a página de gerenciamento de usuários, clientes, templates e orçamentos."""
    st.title("🔑 Painel de Administração")
    
    # --- ABA DE ORÇAMENTOS RESTAURADA ---
    tab1, tab2, tab3, tab4 = st.tabs(["Gerenciar Usuários", "Gerenciar Clientes", "Gerenciar Templates", "Visualizar Orçamentos"])

    with tab1:
        st.write("### Gerenciamento de Usuários")
        users_df = st.session_state.df_usuarios.copy()
        if users_df.empty:
            st.info("Nenhum usuário cadastrado.")
        else:
            # Itera sobre cada usuário para criar um painel de gerenciamento individual
            for index, user in users_df.iterrows():
                st.subheader(f"Usuário: {user['usuario']} ({user['nome_completo']})")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(f"**Status:** {user['status']}")
                    if user['status'] == 'pendente':
                        if st.button("✅ Aprovar", key=f"approve_{user['usuario']}"):
                            st.session_state.df_usuarios.loc[index, 'status'] = 'ativo'
                            storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                            # Salva no GitHub após aprovar
                            storage.save_usuarios_to_github(st.session_state.df_usuarios, st.secrets["github_token"])
                            st.success(f"Usuário {user['usuario']} aprovado!")
                            st.rerun()
                with col2:
                    st.write(f"**Role:** {user['role']}")
                    # Lógica para promover ou rebaixar usuários
                    if user['role'] == 'user':
                        if st.button("⬆️ Promover a Orcamentista", key=f"promote_orc_{user['usuario']}"):
                            st.session_state.df_usuarios.loc[index, 'role'] = 'orcamentista'
                            storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                            storage.save_usuarios_to_github(st.session_state.df_usuarios, st.secrets["github_token"])
                            st.success(f"Usuário {user['usuario']} promovido a Orcamentista!")
                            st.rerun()
                    elif user['role'] == 'orcamentista':
                        c1, c2 = st.columns(2)
                        with c1:
                            if st.button("⬆️ Promover a Admin", key=f"promote_adm_{user['usuario']}"):
                                st.session_state.df_usuarios.loc[index, 'role'] = 'admin'
                                storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                                storage.save_usuarios_to_github(st.session_state.df_usuarios, st.secrets["github_token"])
                                st.success(f"Usuário {user['usuario']} promovido a Admin!")
                                st.rerun()
                        with c2:
                            if st.button("⬇️ Rebaixar para Usuário", key=f"demote_usr_{user['usuario']}"):
                                st.session_state.df_usuarios.loc[index, 'role'] = 'user'
                                storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                                storage.save_usuarios_to_github(st.session_state.df_usuarios, st.secrets["github_token"])
                                st.warning(f"Usuário {user['usuario']} rebaixado para Usuário.")
                                st.rerun()
                with col3:
                    # Impede que o admin desative a si mesmo
                    if user['status'] == 'ativo' and user['usuario'] != st.session_state.username:
                        if st.button("❌ Desativar", key=f"deactivate_{user['usuario']}"):
                            st.session_state.df_usuarios.loc[index, 'status'] = 'inativo'
                            storage.save_csv(st.session_state.df_usuarios, config.USERS_FILE)
                            storage.save_usuarios_to_github(st.session_state.df_usuarios, st.secrets["github_token"])
                            st.warning(f"Usuário {user['usuario']} desativado.")
                            st.rerun()
                st.divider()

    # --- NOVA ABA DE GERENCIAMENTO DE CLIENTES ---
    with tab2:
        st.write("### Gerenciamento de Clientes")
        if 'df_clientes' not in st.session_state or st.session_state.df_clientes.empty:
            st.info("Nenhum cliente cadastrado.")
        else:
            # CORREÇÃO: converte colunas object para número ou string
            df_clientes_admin = st.session_state.df_clientes.copy()
            for col in df_clientes_admin.columns:
                if df_clientes_admin[col].dtype == "object":
                    try:
                        df_clientes_admin[col] = pd.to_numeric(df_clientes_admin[col], errors="raise")
                    except Exception:
                        df_clientes_admin[col] = df_clientes_admin[col].astype(str)

            # Adiciona selectbox para selecionar cliente
            client_list = [""] + st.session_state.df_clientes["Nome"].tolist()
            selected_client_name = st.selectbox("Selecione um cliente para editar ou excluir", client_list, key="admin_select_client")

            if selected_client_name:
                client_index = st.session_state.df_clientes[st.session_state.df_clientes["Nome"] == selected_client_name].index[0]
                client_data = st.session_state.df_clientes.loc[client_index].to_dict()

                st.subheader(f"Editando: {selected_client_name}")
                with st.form("edit_client_form"):
                    # Cria campos de edição para cada dado do cliente
                    edited_data = {}
                    for key, value in client_data.items():
                        edited_data[key] = st.text_input(f"{key}", value=value, key=f"edit_{key}")
                    
                    submitted = st.form_submit_button("Salvar Alterações")
                    if submitted:
                        # Atualiza o DataFrame
                        for key, value in edited_data.items():
                            st.session_state.df_clientes.loc[client_index, key] = value
                        storage.save_csv(st.session_state.df_clientes, config.CLIENTES_FILE)
                        st.success(f"Cliente '{selected_client_name}' atualizado com sucesso!")
                        st.rerun()

                # Lógica de exclusão com confirmação
                st.divider()
                st.subheader(f"Zona de Perigo: Excluir Cliente")
                if st.checkbox(f"Confirmar exclusão de {selected_client_name}", key="delete_client_confirm"):
                    if st.button("Excluir Cliente Permanentemente", type="primary"):
                        st.session_state.df_clientes = st.session_state.df_clientes.drop(index=client_index).reset_index(drop=True)
                        storage.save_csv(st.session_state.df_clientes, config.CLIENTES_FILE)
                        # Exclui do GitHub e reenvia o CSV atualizado
                        storage.delete_cliente_from_github(selected_client_name, st.secrets["github_token"])
                        st.warning(f"Cliente '{selected_client_name}' foi excluído.")
                        st.rerun()

    # --- NOVA ABA DE GERENCIAMENTO DE TEMPLATES ---
    with tab3:
        st.write("### Gerenciamento de Templates de Orçamento")
        if 'df_templates' not in st.session_state or st.session_state.df_templates.empty:
            st.info("Nenhum template salvo.")
        else:
            df_templates_admin = st.session_state.df_templates.copy()
            for col in df_templates_admin.columns:
                if df_templates_admin[col].dtype == "object":
                    try:
                        df_templates_admin[col] = pd.to_numeric(df_templates_admin[col], errors="raise")
                    except Exception:
                        df_templates_admin[col] = df_templates_admin[col].astype(str)

            # Adiciona selectbox para selecionar template
            template_list = [""] + st.session_state.df_templates["NomeTemplate"].tolist()
            selected_template_name = st.selectbox("Selecione um template para editar ou excluir", template_list, key="admin_select_template")

            if selected_template_name:
                template_index = st.session_state.df_templates[st.session_state.df_templates["NomeTemplate"] == selected_template_name].index[0]

                st.subheader(f"Renomear: {selected_template_name}")
                new_name = st.text_input("Novo nome para o template", value=selected_template_name)
                if st.button("Salvar Novo Nome"):
                    if new_name and new_name != selected_template_name:
                        st.session_state.df_templates.loc[template_index, "NomeTemplate"] = new_name
                        storage.save_csv(st.session_state.df_templates, config.TEMPLATES_FILE)
                        st.success(f"Template renomeado para '{new_name}'!")
                        st.rerun()
                    else:
                        st.warning("Por favor, insira um nome novo e diferente.")

                # Lógica de exclusão com confirmação
                st.divider()
                st.subheader(f"Zona de Perigo: Excluir Template")
                if st.checkbox(f"Confirmar exclusão de {selected_template_name}", key="delete_template_confirm"):
                    if st.button("Excluir Template Permanentemente", type="primary"):
                        st.session_state.df_templates = st.session_state.df_templates.drop(index=template_index).reset_index(drop=True)
                        storage.save_csv(st.session_state.df_templates, config.TEMPLATES_FILE)
                        storage.delete_template_from_github(selected_template_name, st.secrets["github_token"])
                        st.warning(f"Template '{selected_template_name}' foi excluído.")
                        st.rerun()

     # --- NOVA ABA PARA VISUALIZAR TODOS OS ORÇAMENTOS ---
    with tab4:
        st.write("### Histórico Completo de Orçamentos")
        if 'df_orcamentos' not in st.session_state or st.session_state.df_orcamentos.empty:
            st.info("Nenhum orçamento foi salvo na aplicação ainda.")
        else:
            df_display_admin = st.session_state.df_orcamentos[[
                "NomeOrcamentista", "Cliente", "Quantidade", "Produto", "Data", "PropostaPDF"
            ]].copy()
            df_display_admin.rename(columns={
                "NomeOrcamentista": "Orçamentista",
                "Cliente": "Cliente",
                "Quantidade": "Qtd.",
                "Produto": "Produto",
                "Data": "Data",
                "PropostaPDF": "Proposta PDF"
            }, inplace=True)
            # CORREÇÃO: converte colunas object para número ou string
            for col in df_display_admin.columns:
                if df_display_admin[col].dtype == "object":
                    try:
                        df_display_admin[col] = pd.to_numeric(df_display_admin[col], errors="raise")
                    except Exception:
                        df_display_admin[col] = df_display_admin[col].astype(str)
            st.dataframe(df_display_admin, width='stretch', hide_index=True)

            with st.expander("Ver Detalhes Completos de um Orçamento"):
                orcamento_completo = st.session_state.df_orcamentos
                id_orcamento_admin = st.selectbox("Selecione o ID do Orçamento", options=orcamento_completo['ID'], key="admin_orc_select")
                if id_orcamento_admin:
                    orcamento_selecionado_admin = orcamento_completo[orcamento_completo['ID'] == id_orcamento_admin].iloc[0]
                    df_detalhes_admin = orcamento_selecionado_admin.drop('AjustesJSON').to_frame().T.copy()
                    for col in df_detalhes_admin.columns:
                        if df_detalhes_admin[col].dtype == "object":
                            try:
                                df_detalhes_admin[col] = pd.to_numeric(df_detalhes_admin[col], errors="raise")
                            except Exception:
                                df_detalhes_admin[col] = df_detalhes_admin[col].astype(str)
                    st.dataframe(df_detalhes_admin)
                    
                    # Mostra status colorido no topo do expander
                    status = orcamento_selecionado_admin.get('StatusOrcamento', 'Pendente')
                    if pd.isna(status):
                        status = "Pendente"
                    status = str(status).strip().capitalize()
                    status_colors = {
                        "Pendente": "#ff9800",
                        "Aprovado": "#2ecc40",
                        "Suspenso": "#ffeb3b",
                        "Finalizado": "#e74c3c"
                    }
                    st.markdown(
                        f"<span style='color:{status_colors.get(status, '#222')};font-weight:bold;font-size:1.1em;'>Status: {status}</span>",
                        unsafe_allow_html=True
                    )

                    # Botão para baixar o PDF da proposta, se existir
                    pdf_path = orcamento_selecionado_admin.get("PropostaPDF")
                    # Garante que pdf_path é string válida e não NaN/None
                    import math
                    if pdf_path is None or (isinstance(pdf_path, float) and math.isnan(pdf_path)):
                        pdf_path = ""
                    try:
                        if isinstance(pdf_path, str) and pdf_path and os.path.exists(pdf_path):
                            with open(pdf_path, "rb") as fpdf:
                                st.download_button("Baixar Proposta PDF", fpdf, file_name=os.path.basename(pdf_path), key=f"download_pdf_{id_orcamento_admin}")
                    except Exception:
                        pass

                    # Regras de exibição dos botões
                    # Pendente: Baixar, Editar, Excluir, Aprovar
                    # Aprovado: Baixar, Editar, Suspender, Finalizar, Gerar Ordem
                    # Suspenso: Baixar, Editar, Excluir, Aprovar, Finalizar, Gerar Ordem
                    # Finalizado: Baixar, Editar, Gerar Ordem

                    btns = []
                    if status == "Pendente":
                        btns = ["editar", "excluir", "aprovar"]
                    elif status == "Aprovado":
                        btns = ["editar", "suspender", "finalizar", "ordem"]
                    elif status == "Suspenso":
                        btns = ["editar", "excluir", "aprovar", "finalizar", "ordem"]
                    elif status == "Finalizado":
                        btns = ["editar", "ordem"]

                    cols = st.columns(len(btns)) if btns else []

                    # Removido CSS customizado para não pintar todos os botões

                    for idx, btn in enumerate(btns):
                        with cols[idx]:
                            if btn == "editar":
                                if st.button("Editar esta versão", key=f"editar_{id_orcamento_admin}_details"):
                                    # ...existing code for editar...
                                    st.rerun()
                                st.markdown('<style>div[data-testid="stButton"] button {background-color: #1976d2 !important; color: #fff !important;}</style>', unsafe_allow_html=True)
                            elif btn == "excluir":
                                if st.button("Excluir Orçamento", key=f"excluir_{id_orcamento_admin}_details"):
                                    idx_del = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento_admin].index[0]
                                    st.session_state.df_orcamentos = st.session_state.df_orcamentos.drop(idx_del).reset_index(drop=True)
                                    storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                                    storage.delete_orcamento_from_github(st.secrets["github_token"])
                                    st.success(f"Orçamento {id_orcamento_admin} excluído com sucesso!")
                                    st.rerun()
                                st.markdown('<style>div[data-testid="stButton"] button {background-color: #f44336 !important; color: #fff !important;}</style>', unsafe_allow_html=True)
                            elif btn == "aprovar":
                                if st.button("Aprovar Orçamento", key=f"aprovar_{id_orcamento_admin}_details"):
                                    idx_apr = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento_admin].index[0]
                                    st.session_state.df_orcamentos.loc[idx_apr, "StatusOrcamento"] = "Aprovado"
                                    storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                                    storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                                    st.success(f"Orçamento {id_orcamento_admin} aprovado!")
                                    st.rerun()
                                st.markdown('<style>div[data-testid="stButton"] button {background-color: #2ecc40 !important; color: #fff !important;}</style>', unsafe_allow_html=True)
                            elif btn == "suspender":
                                if st.button("Suspender Orçamento", key=f"suspender_{id_orcamento_admin}_details"):
                                    idx_sus = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento_admin].index[0]
                                    st.session_state.df_orcamentos.loc[idx_sus, "StatusOrcamento"] = "Suspenso"
                                    storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                                    storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                                    st.success(f"Orçamento {id_orcamento_admin} suspenso!")
                                    st.rerun()
                                st.markdown('<style>div[data-testid="stButton"] button {background-color: #ffeb3b !important; color: #222 !important;}</style>', unsafe_allow_html=True)
                            elif btn == "finalizar":
                                if st.button("Finalizar Orçamento", key=f"finalizar_{id_orcamento_admin}_details"):
                                    idx_fin = st.session_state.df_orcamentos[st.session_state.df_orcamentos['ID'] == id_orcamento_admin].index[0]
                                    st.session_state.df_orcamentos.loc[idx_fin, "StatusOrcamento"] = "Finalizado"
                                    storage.save_csv(st.session_state.df_orcamentos, config.ORCAMENTOS_FILE)
                                    storage.save_orcamentos_to_github(st.session_state.df_orcamentos, st.secrets["github_token"])
                                    st.success(f"Orçamento {id_orcamento_admin} finalizado!")
                                    st.rerun()
                                st.markdown('<style>div[data-testid="stButton"] button {background-color: #e74c3c !important; color: #fff !important;}</style>', unsafe_allow_html=True)
                            elif btn == "ordem":
                                custom_btn_style = f"""
                                <style>
                                div[data-testid="stButton"] button#gerar_ordem_prototipo_{id_orcamento_admin} {{
                                    background-color: #fff !important;
                                    color: #222 !important;
                                    border: 1px solid #ccc !important;
                                }}
                                </style>
                                """
                                st.markdown(custom_btn_style, unsafe_allow_html=True)
                                if st.button("Gerar Ordem de Protótipo", key=f"gerar_ordem_prototipo_{id_orcamento_admin}"):
                                    from generate_ordem_prototipo import generate_ordem_prototipo_pdf
                                    import os
                                    from datetime import datetime
                                    proposta_data = {
                                        "data": datetime.now().strftime("%d/%m/%Y"),
                                        "cliente": orcamento_selecionado_admin.get("Cliente", ""),
                                        "responsavel": "",
                                        "numero_orcamento": orcamento_selecionado_admin.get("ID", ""),
                                        "versao_orcamento": orcamento_selecionado_admin.get("VersoesOrcamento", 1),
                                        "produto": orcamento_selecionado_admin.get("Produto", ""),
                                        "quantidade": 2,
                                        "descrição": orcamento_selecionado_admin.get("descrição", ""),
                                        "Unitario": orcamento_selecionado_admin.get("PrecoVenda", ""),
                                        "total": "",
                                        "atendente": orcamento_selecionado_admin.get("NomeOrcamentista", ""),
                                        "validade": "",
                                        "prazo_de_entrega": "",
                                    }
                                    try:
                                        cliente_row = st.session_state.df_clientes[
                                            st.session_state.df_clientes["Nome"] == orcamento_selecionado_admin.get("Cliente", "")
                                        ]
                                        if not cliente_row.empty:
                                            proposta_data["responsavel"] = cliente_row["Contato"].values[0]
                                    except Exception:
                                        pass
                                    propostas_dir = "Propostas"
                                    if not os.path.exists(propostas_dir):
                                        os.makedirs(propostas_dir, exist_ok=True)
                                    ordem_path = os.path.join(
                                        propostas_dir,
                                        f"OrdemPrototipo_{proposta_data['cliente']}_{proposta_data['produto']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                    )
                                    generate_ordem_prototipo_pdf(proposta_data, ordem_path)
                                    if os.path.exists(ordem_path):
                                        with open(ordem_path, "rb") as fpdf:
                                            st.download_button(
                                                "Baixar Ordem de Protótipo PDF",
                                                fpdf,
                                                file_name=os.path.basename(ordem_path),
                                                key=f"download_ordem_{id_orcamento_admin}"
                                            )