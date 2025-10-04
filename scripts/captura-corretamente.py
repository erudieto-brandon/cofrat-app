import re

# --- FUNÇÃO DE EXTRAÇÃO DE BLOCO (Sua versão original, sem alterações) ---
def parse_appointment_block(block_lines):
    if len(block_lines) < 6:
        return None
    EVENT_TYPES = ["CONSULTA", "RETORNO"]
    event_doctor_line = block_lines[4]
    event, doctor = None, None
    for event_type in EVENT_TYPES:
        if event_doctor_line.upper().startswith(event_type):
            event = event_type
            doctor = event_doctor_line[len(event_type):].strip()
            break
    if event is None:
        parts = event_doctor_line.split(maxsplit=1)
        event = parts[0]
        doctor = parts[1] if len(parts) > 1 else ""
    record = {
        "time": block_lines[0], "patient": block_lines[1], "insurance": block_lines[2],
        "patient_phone": block_lines[3].strip(' -'), "event": event, "doctor": doctor,
        "record": block_lines[5]
    }
    return record

# --- CÓDIGO PRINCIPAL (Seu código com a correção no loop) ---
texto_completo = items[0]['json']['text']
linhas = [line.strip() for line in texto_completo.split('\n') if line.strip()]

agendamentos_finalizados = []
data_atual = ""
especialidade_atual = ""

# Regex e constantes
regex_hora = re.compile(r'^\d{2}:\d{2}$') 
regex_data = re.compile(r'\d{2}/\d{2}/\d{4}')
HEADER_INDICATORS = ("Página", "SIMAH", "Agendamentos de Consultas")
lixo_prefixos = ("Página", "SIMAH", "Agendamentos de Consultas", "COFRAT", "Sub - Total",
                 "Médico", "Paciente", "Convênio", "Telefone do Paciente", "Evento", "Prontuário")

def is_near_header(idx, context_lines=3):
    for k in range(0, context_lines):
        j = idx - k
        if j < 0: break
        if any(ind in linhas[j] for ind in HEADER_INDICATORS):
            return True
    return False

# --- LOOP ---
i = 0
while i < len(linhas):
    linha = linhas[i]

    # Lógica de ignorar lixo (mantida)
    if any(linha.startswith(prefixo) for prefixo in lixo_prefixos):
        i += 1
        continue

    # Lógica de captura de data (mantida)
    match_data = regex_data.search(linha)
    if match_data and not is_near_header(i):
        data_atual = match_data.group(0)
        i += 1
        continue

    # Lógica de captura de especialidade (mantida)
    if "Especialidade" in linha:
        parts = linha.split("Especialidade", 1)
        specialty_candidate = parts[1].lstrip(':').strip() if len(parts) > 1 else ""
        if specialty_candidate:
            especialidade_atual = specialty_candidate
        elif i + 1 < len(linhas):
            especialidade_atual = linhas[i+1].strip()
            i += 1
        i += 1
        continue

    # --- LÓGICA DE CAPTURA DE AGENDAMENTO (COM A CORREÇÃO FINAL) ---
    if regex_hora.match(linha):
        if i + 5 < len(linhas):
            # **A CORREÇÃO ESTÁ AQUI: Verificação de segurança antes de processar**
            # Se a 6ª linha for um horário, o bloco está corrompido.
            if regex_hora.match(linhas[i+5]):
                # Processa um bloco de 5 linhas, adicionando uma 6ª linha vazia para o prontuário.
                bloco_corrompido = linhas[i : i + 5] + [""] 
                agendamento = parse_appointment_block(bloco_corrompido)
                if agendamento:
                    agendamento['date'] = data_atual
                    agendamento['specialty'] = especialidade_atual
                    agendamentos_finalizados.append(agendamento)
                # Avança 5 linhas, pois foi o que consumimos.
                i += 5
                continue
            else:
                # O bloco é normal, processa como antes.
                bloco_de_linhas = linhas[i : i + 6]
                agendamento = parse_appointment_block(bloco_de_linhas)
                if agendamento:
                    agendamento['date'] = data_atual
                    agendamento['specialty'] = especialidade_atual
                    agendamentos_finalizados.append(agendamento)
                # Avança 6 linhas.
                i += 6
                continue

    # Se a linha não foi processada por nenhuma regra acima, avança 1.
    i += 1

# --- RETORNO ---
return [{"json": ag} for ag in agendamentos_finalizados]