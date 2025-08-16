from datetime import datetime

from models import Conversation, Commande


# ---------------------- MODELS HELPERS ----------------------

def test_conversation_methods():
    conv = Conversation(client_name="Client")
    conv.add_message("user", "hello")
    conv.add_message("assistant", "hi", image_path="path.png")
    assert conv.history[0]["content"] == "hello"
    assert conv.history[1]["image_path"] == "path.png"
    assert conv.updated_at is None
    conv.set_status("en_cours")
    assert conv.status == "en_cours"
    assert isinstance(conv.updated_at, datetime)


def test_commande_repr():
    cmd = Commande(numero_commande="CMD1", user_id=1, montant_ht=10, montant_ttc=12)
    assert repr(cmd) == "<Commande CMD1>"
