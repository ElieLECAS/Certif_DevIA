from django.db import models

# Définir le routeur de base de données pour les modèles
class CommandeRouter:
    db_name = 'commande'

class StammRouter:
    db_name = 'stamm'

class AKopf(models.Model):
    """
    Modèle représentant la table dbo.A_Kopf contenant les informations principales des commandes.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=32, db_collation='French_CI_AS')
    auftragstyp = models.SmallIntegerField(db_column='AuftragsTyp', blank=True, null=True)
    aunummer = models.IntegerField(db_column='AuNummer', blank=True, null=True, verbose_name="Numéro de commande")
    aualpha = models.CharField(db_column='AuAlpha', max_length=5, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Extension")
    kundennr = models.CharField(db_column='KundenNr', max_length=15, db_collation='French_CI_AS', blank=True, null=True)
    kundenbez = models.CharField(db_column='KundenBez', max_length=15, db_collation='French_CI_AS', blank=True, null=True)
    kommission = models.CharField(db_column='Kommission', max_length=50, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Affaire")
    bauvorhaben = models.CharField(db_column='Bauvorhaben', max_length=50, db_collation='French_CI_AS', blank=True, null=True)
    auftragsart = models.SmallIntegerField(db_column='Auftragsart', blank=True, null=True)
    fsystemgrp = models.SmallIntegerField(db_column='FSystemGrp', blank=True, null=True)
    aufstatus = models.CharField(db_column='AufStatus', max_length=15, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Statut")
    techniker = models.CharField(db_column='Techniker', max_length=15, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Technicien")
    a_vormwst = models.DecimalField(db_column='A_VorMwSt', max_digits=15, decimal_places=2, blank=True, null=True, verbose_name="Prix HT")

    class Meta:
        db_table = 'A_Kopf'
        managed = False
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        app_label = 'suivi'
        db_table_comment = "Table principale des commandes"
        db_tablespace = None
        unique_together = (('auftragstyp', 'aunummer', 'aualpha'),)

    def __str__(self):
        return f"{self.aunummer}{self.aualpha} - {self.aufstatus}"

class ALogbuch(models.Model):
    """
    Modèle représentant la table dbo.A_Logbuch contenant les informations de log des commandes.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.AutoField(primary_key=True)
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='alogbuch')
    code = models.CharField(db_column='Code', max_length=15, db_collation='French_CI_AS', blank=True, null=True)  # Field name made lowercase.
    bezeichnung = models.CharField(db_column='Bezeichnung', max_length=50, db_collation='French_CI_AS', blank=True, null=True)  # Field name made lowercase.
    datum = models.DateTimeField(db_column='Datum', blank=True, null=True)  # Field name made lowercase.
    zeit = models.DateTimeField(db_column='Zeit', blank=True, null=True)  # Field name made lowercase.
    benutzer = models.CharField(db_column='Benutzer', max_length=50, db_collation='French_CI_AS', blank=True, null=True)  # Field name made lowercase.
    notiz = models.TextField(db_column='Notiz', db_collation='French_CI_AS', blank=True, null=True)  # Field name made lowercase.

    class Meta:
        managed = False
        db_table = 'A_Logbuch'
        verbose_name = "Log de commande"
        verbose_name_plural = "Logs de commandes"
        app_label = 'suivi'



class AKopffreie(models.Model):
    """
    Modèle représentant la table dbo.A_KopfFreie contenant des informations additionnelles sur les commandes.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='akopffreie')
    nummer = models.SmallIntegerField(db_column='Nummer')
    feldtyp = models.IntegerField(db_column='FeldTyp', blank=True, null=True)
    feldinhalt = models.CharField(db_column='FeldInhalt', max_length=50, db_collation='French_CI_AS', blank=True, null=True)
    feld1 = models.CharField(db_column='Feld1', max_length=50, db_collation='French_CI_AS', blank=True, null=True)
    feld2 = models.CharField(db_column='Feld2', max_length=50, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Nombre de menuiseries")
    feld3 = models.CharField(db_column='Feld3', max_length=50, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Date d'entrée")
    feld5 = models.CharField(db_column='Feld5', max_length=50, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Date de livraison")

    class Meta:
        db_table = 'A_KopfFreie'
        managed = False
        verbose_name = "Information additionnelle de commande"
        verbose_name_plural = "Informations additionnelles de commandes"
        app_label = 'suivi'
        unique_together = (('id_a_kopf', 'nummer'),)

    def __str__(self):
        return f"Info additionnelle: {self.id_a_kopf}"


class AAdresse(models.Model):
    """
    Modèle représentant la table dbo.A_Adresse contenant les informations d'adresse des clients.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='adresses')
    nummer = models.SmallIntegerField(db_column='Nummer')
    adressnummer = models.CharField(db_column='Adressnummer', max_length=15, db_collation='French_CI_AS', blank=True, null=True)
    adresscode = models.CharField(db_column='AdressCode', max_length=50, db_collation='French_CI_AS', blank=True, null=True)
    firma = models.CharField(db_column='Firma', max_length=50, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Client")
    telefon = models.CharField(db_column='Telefon', max_length=30, db_collation='French_CI_AS', blank=True, null=True)
    email = models.CharField(db_column='Email', max_length=100, db_collation='French_CI_AS', blank=True, null=True)

    class Meta:
        db_table = 'A_Adresse'
        managed = False
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
        app_label = 'suivi'
        unique_together = (('id_a_kopf', 'nummer'),)

    def __str__(self):
        return f"Adresse: {self.firma}"


class AVorgang(models.Model):
    """
    Modèle représentant la table dbo.A_Vorgang contenant les informations d'événements sur les commandes.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='vorgangen')
    nummer = models.CharField(db_column='Nummer', max_length=15, db_collation='French_CI_AS')
    bezeichnung = models.CharField(db_column='Bezeichnung', max_length=50, db_collation='French_CI_AS', blank=True, null=True)
    datum = models.DateTimeField(db_column='Datum', blank=True, null=True, verbose_name="Date")
    zeit = models.DateTimeField(db_column='Zeit', blank=True, null=True, verbose_name="Heure")
    benutzer = models.CharField(db_column='Benutzer', max_length=50, db_collation='French_CI_AS', blank=True, null=True)
    notizcode = models.CharField(db_column='NotizCode', max_length=15, db_collation='French_CI_AS', blank=True, null=True)
    notiztext = models.TextField(db_column='NotizText', db_collation='French_CI_AS', blank=True, null=True)
    codeintern = models.CharField(db_column='CodeIntern', max_length=15, db_collation='French_CI_AS', blank=True, null=True)
    nloesch = models.SmallIntegerField(db_column='NLoesch', blank=True, null=True)

    class Meta:
        db_table = 'A_Vorgang'
        managed = False
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        app_label = 'suivi'
        unique_together = (('id_a_kopf', 'nummer'),)

    def __str__(self):
        return f"{self.nummer} - {self.datum}"


class PArtikel(models.Model):
    """
    Modèle représentant la table dbo.P_Artikel contenant les informations sur les articles utilisés.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='articles')
    position = models.IntegerField(db_column='Position', verbose_name="Position")
    artikelid = models.CharField(db_column='ArtikelID', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="ID Article")
    dim1 = models.IntegerField(db_column='Dim1', blank=True, null=True, verbose_name="Dimension 1")
    dim2 = models.IntegerField(db_column='Dim2', blank=True, null=True, verbose_name="Dimension 2")
    dim3 = models.IntegerField(db_column='Dim3', blank=True, null=True, verbose_name="Dimension 3")

    class Meta:
        db_table = 'P_Artikel'
        managed = False
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        app_label = 'suivi'
 
    def __str__(self):
        return f"{self.artikelid} (Pos: {self.position})"


class PKaufm(models.Model):
    """
    Modèle représentant la table dbo.P_Kaufm contenant les informations commerciales.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='kaufm')
    position = models.IntegerField(db_column='Position', verbose_name="Position")
    stueck = models.IntegerField(db_column='Stueck', blank=True, null=True, verbose_name="Quantité")

    class Meta:
        db_table = 'P_Kaufm'
        managed = False
        verbose_name = "Information commerciale"
        verbose_name_plural = "Informations commerciales"
        app_label = 'suivi'

    def __str__(self):
        return f"Info commerciale: Pos {self.position}"


class PWerkstoffe(models.Model):
    """
    Modèle représentant la table dbo.P_Werkstoffe contenant les informations sur les matériaux.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='werkstoffe')
    position = models.IntegerField(db_column='Position', verbose_name="Position")
    farbe1 = models.CharField(db_column='Farbe1', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Couleur")

    class Meta:
        db_table = 'P_Werkstoffe'
        managed = False
        verbose_name = "Matériau"
        verbose_name_plural = "Matériaux"
        app_label = 'suivi'

    def __str__(self):
        return f"Matériau: Pos {self.position}"


class PTeil(models.Model):
    """
    Modèle représentant la table dbo.P_Teil contenant les informations sur les variantes.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='teilen')
    position = models.IntegerField(db_column='Position', verbose_name="Position")
    variante = models.CharField(db_column='Variante', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Variante")
    oberfl = models.CharField(db_column='Oberfl', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Extérieur")
    oberfli = models.CharField(db_column='Oberfli', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Intérieur")

    class Meta:
        db_table = 'P_Teil'
        managed = False
        verbose_name = "Partie"
        verbose_name_plural = "Parties"
        app_label = 'suivi'

    def __str__(self):
        return f"Partie: Pos {self.position}"


class PProfile1(models.Model):
    """
    Modèle représentant la table dbo.P_Profile1 contenant les informations sur les profils.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='profiles')
    profiltyp = models.CharField(db_column='ProfilTyp', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Type de profil")
    profilflgtyp = models.CharField(db_column='ProfilFlgTyp', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Type de profil FLG")

    class Meta:
        db_table = 'P_Profile1'
        managed = False
        verbose_name = "Profil"
        verbose_name_plural = "Profils"
        app_label = 'suivi'

    def __str__(self):
        return f"Profil: {self.profiltyp or self.profilflgtyp}"


class PAnschluss(models.Model):
    """
    Modèle représentant la table dbo.P_Anschluss contenant les informations sur les raccords.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='anschluss')
    code = models.CharField(db_column='Code', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Code")

    class Meta:
        db_table = 'P_Anschluss'
        managed = False
        verbose_name = "Raccord"
        verbose_name_plural = "Raccords"
        app_label = 'suivi'

    def __str__(self):
        return f"Raccord: {self.code}"


class PGLeisten(models.Model):
    """
    Modèle représentant la table dbo.P_GLeisten contenant les informations sur les listels.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='gleisten')
    typ = models.CharField(db_column='Typ', max_length=255, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Type")

    class Meta:
        db_table = 'P_GLeisten'
        managed = False
        verbose_name = "Listel"
        verbose_name_plural = "Listels"
        app_label = 'suivi'

    def __str__(self):
        return f"Listel: {self.typ}"


# Modèles pour la base de données Stamm
class SArtikel(models.Model):
    """
    Modèle représentant la table dbo.S_Artikel de la base Stamm contenant la liste des articles.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = StammRouter
    
    artikelid = models.CharField(db_column='ArtikelID', primary_key=True, max_length=255, db_collation='French_CI_AS', verbose_name="ID Article")

    class Meta:
        db_table = 'S_Artikel'
        managed = False
        verbose_name = "Article (Stamm)"
        verbose_name_plural = "Articles (Stamm)"
        app_label = 'suivi'

    def __str__(self):
        return self.artikelid


class FenTeil(models.Model):
    """
    Modèle représentant la table dbo.FenTeil de la base Stamm contenant la liste des profils.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = StammRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    artikelid = models.CharField(db_column='ArtikelID', max_length=255, db_collation='French_CI_AS', verbose_name="ID Article")

    class Meta:
        db_table = 'FenTeil'
        managed = False
        verbose_name = "Profil (Stamm)"
        verbose_name_plural = "Profils (Stamm)"
        app_label = 'suivi'

    def __str__(self):
        return self.artikelid


class SZubehoer(models.Model):
    """
    Modèle représentant la table dbo.S_Zubehoer de la base Stamm contenant la liste des accessoires.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = StammRouter
    
    id = models.CharField(db_column='ID', primary_key=True, max_length=36, db_collation='French_CI_AS')
    code = models.CharField(db_column='Code', max_length=255, db_collation='French_CI_AS', verbose_name="Code")
    artikel = models.CharField(db_column='Artikel', max_length=255, db_collation='French_CI_AS', verbose_name="Article")

    class Meta:
        db_table = 'S_Zubehoer'
        managed = False
        verbose_name = "Accessoire"
        verbose_name_plural = "Accessoires"
        app_label = 'suivi'

    def __str__(self):
        return f"{self.code} - {self.artikel}"


class PZubeh(models.Model):
    """
    Modèle représentant la table dbo.P_Zubeh contenant les informations sur les accessoires des commandes.
    """
    # Définir explicitement la base de données à utiliser
    DatabaseRouter = CommandeRouter
    
    id_a_kopf = models.ForeignKey(AKopf, on_delete=models.CASCADE, db_column='ID_A_Kopf', related_name='pzubeh')
    position = models.SmallIntegerField(db_column='Position', verbose_name="Position")
    kennung = models.SmallIntegerField(db_column='Kennung', verbose_name="Kennung")
    znr = models.SmallIntegerField(db_column='ZNr', verbose_name="ZNr")
    zcode = models.CharField(db_column='ZCode', max_length=20, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Code Accessoire")
    text = models.CharField(db_column='Text', max_length=50, db_collation='French_CI_AS', blank=True, null=True, verbose_name="Texte")
    stueck = models.FloatField(db_column='Stueck', blank=True, null=True, verbose_name="Quantité")

    class Meta:
        db_table = 'P_Zubeh'
        managed = False
        verbose_name = "Accessoire de commande"
        verbose_name_plural = "Accessoires de commandes"
        app_label = 'suivi'
        unique_together = (('id_a_kopf', 'position', 'kennung', 'znr'),)

    def __str__(self):
        return f"{self.zcode} - {self.text}"
