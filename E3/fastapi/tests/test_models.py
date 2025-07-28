import pytest
from models import User, Conversation, Commande, ClientUser
from auth import get_password_hash
from datetime import datetime

class TestUserModel:
    """Tests pour le modèle User"""
    
    def test_user_creation(self):
        """Test de création d'un utilisateur"""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass"),
            is_active=True,
            is_staff=False,
            is_superuser=False
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        # created_at sera défini lors de la sauvegarde en DB
        assert hasattr(user, 'created_at')
    
    def test_user_with_client_info(self):
        """Test d'un utilisateur avec informations client"""
        user = User(
            username="client1",
            email="client@example.com",
            hashed_password=get_password_hash("clientpass"),
            nom="Dupont",
            prenom="Jean",
            telephone="0123456789",
            adresse="123 Rue de la Paix, Paris"
        )
        
        assert user.nom == "Dupont"
        assert user.prenom == "Jean"
        assert user.telephone == "0123456789"
        assert user.adresse == "123 Rue de la Paix, Paris"

class TestConversationModel:
    """Tests pour le modèle Conversation"""
    
    def test_conversation_creation(self):
        """Test de création d'une conversation"""
        conversation = Conversation(
            client_name="Test Client",
            status="nouveau",
            user_id=1
        )
        
        assert conversation.client_name == "Test Client"
        assert conversation.status == "nouveau"
        assert conversation.user_id == 1
        # history sera initialisé lors de la sauvegarde
        assert hasattr(conversation, 'history')
        # created_at et updated_at seront définis lors de la sauvegarde
        assert hasattr(conversation, 'created_at')
        assert hasattr(conversation, 'updated_at')
    
    def test_conversation_add_message(self):
        """Test d'ajout de message à une conversation"""
        conversation = Conversation(
            client_name="Test Client",
            status="nouveau"
        )
        
        conversation.add_message("user", "Bonjour")
        conversation.add_message("assistant", "Bonjour ! Comment puis-je vous aider ?")
        
        assert len(conversation.history) == 2
        assert conversation.history[0]["role"] == "user"
        assert conversation.history[0]["content"] == "Bonjour"
        assert conversation.history[1]["role"] == "assistant"
    
    def test_conversation_set_status(self):
        """Test de changement de statut"""
        conversation = Conversation(
            client_name="Test Client",
            status="nouveau"
        )
        
        conversation.set_status("en_cours")
        assert conversation.status == "en_cours"
        assert conversation.updated_at is not None

class TestCommandeModel:
    """Tests pour le modèle Commande"""
    
    def test_commande_creation(self):
        """Test de création d'une commande"""
        commande = Commande(
            numero_commande="CMD-2024-001",
            user_id=1,
            montant_ht=100.0,
            montant_ttc=120.0,
            statut="en_cours",
            produits=[{"nom": "Produit 1", "prix": 100.0}],
            adresse_livraison="123 Rue de la Paix, Paris",
            notes="Commande urgente"
        )
        
        assert commande.numero_commande == "CMD-2024-001"
        assert commande.user_id == 1
        assert commande.montant_ht == 100.0
        assert commande.montant_ttc == 120.0
        assert commande.statut == "en_cours"
        assert len(commande.produits) == 1
        assert commande.adresse_livraison == "123 Rue de la Paix, Paris"
        assert commande.notes == "Commande urgente"
    
    def test_commande_repr(self):
        """Test de la représentation string d'une commande"""
        commande = Commande(
            numero_commande="TEST-001",
            user_id=1,
            montant_ht=100.0,
            montant_ttc=120.0
        )
        
        assert str(commande) == "<Commande TEST-001>"

class TestClientUserModel:
    """Tests pour le modèle ClientUser"""
    
    def test_client_user_creation(self):
        """Test de création d'un profil client"""
        client_user = ClientUser(
            user_id=1,
            is_client_only=True,
            active_conversation_id=None
        )
        
        assert client_user.user_id == 1
        assert client_user.is_client_only is True
        assert client_user.active_conversation_id is None
        # created_at sera défini lors de la sauvegarde en DB
        assert hasattr(client_user, 'created_at')
    
    def test_client_user_with_active_conversation(self):
        """Test d'un client avec conversation active"""
        client_user = ClientUser(
            user_id=1,
            is_client_only=True,
            active_conversation_id=5
        )
        
        assert client_user.active_conversation_id == 5 