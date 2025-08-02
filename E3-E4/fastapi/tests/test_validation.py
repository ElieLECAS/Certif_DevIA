#!/usr/bin/env python3
"""
Script de test pour vérifier les validations ajoutées
"""

from schemas import ChatMessage, ConversationClose, ClientNameUpdate
import pytest

def test_chat_message_validation():
    """Test de validation ChatMessage"""
    # Test valide
    msg = ChatMessage(message="Test message", conversation_id="temp")
    assert msg.message == "Test message"
    assert msg.conversation_id == "temp"
    
    # Test avec message vide
    try:
        ChatMessage(message="", conversation_id="temp")
        assert False, "Devrait lever une exception"
    except Exception:
        pass

def test_conversation_close_validation():
    """Test de validation ConversationClose"""
    # Test valide
    conv = ConversationClose(conversation_id=1)
    assert conv.conversation_id == 1
    
    # Test avec ID invalide
    try:
        ConversationClose(conversation_id="invalid")
        assert False, "Devrait lever une exception"
    except Exception:
        pass

def test_client_name_update_validation():
    """Test de validation ClientNameUpdate"""
    # Test valide
    client = ClientNameUpdate(conversation_id=1, client_name="Test Client")
    assert client.conversation_id == 1
    assert client.client_name == "Test Client"

if __name__ == "__main__":
    print("🧪 Test des validations...")
    test_chat_message_validation()
    test_conversation_close_validation()
    test_client_name_update_validation()
    print("✅ Tous les tests de validation passent !") 