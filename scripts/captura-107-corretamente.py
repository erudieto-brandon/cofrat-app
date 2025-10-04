import re

# --- FUNÇÃO DE EXTRAÇÃO DE BLOCO ---
def parse_appointment_block(block_lines):
    """
    Recebe um bloco de 6 linhas e extrai os campos do agendamento.
    """
    if len(block_lines) < 6:
        return None

    EVENT_TYPES = ["CONSULTA", "RETORNO"]
    
    event_doctor_line = block_lines[4]
    event = None
    doctor = None

    # Tenta dividir a linha "Evento+Médico"
    for event_type in EVENT_TYPES:
        if event_doctor_line.upper().startswith(event_type):
            event = event_type
            doctor = event_doctor_line[len(event_type):].strip()
            break
    
    # Fallback se não encontrou tipo
    if event is None:
        parts = event_doctor_line.split(maxsplit=1)
        event = parts[0]
        doctor = parts[1] if len(parts) > 1 else ""

    record = {
        "time": block_lines[0],
        "patient": block_lines[1],
        "insurance": block_lines[2],
        "patient_phone": block_lines[3].strip(' -'),
        "event": event,
        "doctor": doctor,
        "record": block_lines[5]
    }
    return record


# --- CÓDIGO PRINCIPAL ---
texto_completo = items[0]['json']['text']
linhas = [line.strip() for line in texto_completo.split('\n') if line.strip()]

agendamentos_finalizados = []
data_atual = ""
especialidade_atual = ""

# Regex
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

    # ignora lixo
    if any(linha.startswith(prefixo) for prefixo in lixo_prefixos):
        i += 1
        continue

    # --- captura de data ---
    match_data = regex_data.search(linha)
    if match_data and not is_near_header(i):
        data_atual = match_data.group(0)
        i += 1
        continue

    # --- captura de especialidade ---
    if "Especialidade" in linha:
        parts = linha.split("Especialidade", 1)
        if len(parts) > 1:
            especialidade_atual = parts[1].lstrip(':').strip()
        else:
            if i + 1 < len(linhas):
                especialidade_atual = linhas[i+1].strip()
                i += 1
        i += 1
        continue

    # --- captura de agendamento (bloco de 6 linhas) ---
    if regex_hora.match(linha):
        if i + 5 < len(linhas):
            bloco_de_linhas = linhas[i : i + 6]
            agendamento = parse_appointment_block(bloco_de_linhas)
            if agendamento:
                agendamento['date'] = data_atual
                agendamento['specialty'] = especialidade_atual
                agendamentos_finalizados.append(agendamento)
            i += 6
        else:
            i += 1
    else:
        i += 1

# --- RETORNO ---
return [{"json": ag} for ag in agendamentos_finalizados]
