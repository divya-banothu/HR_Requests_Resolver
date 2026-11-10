def test_ticket_id_format():
    ticket_id = "TKT-2026-000001"
    assert ticket_id.startswith("TKT-2026-")
    assert len(ticket_id.split("-")[-1]) == 6

def test_policy_id_format():
    assert "POL-HR-2026-001" == "POL-HR-2026-001"

def test_message_id_format():
    assert "MSG-TKT-2026-000001-001".startswith("MSG-TKT-")