import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, timedelta
import json

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Production Industrielle",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configuration de l'API
API_BASE_URL = "http://api:8000"

# Fonctions utilitaires pour appeler l'API
@st.cache_data(ttl=60)  # Cache pendant 1 minute
def get_centres_usinage():
    """Récupérer la liste des centres d'usinage"""
    try:
        response = requests.get(f"{API_BASE_URL}/centres-usinage/")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API: {e}")
        return []

@st.cache_data(ttl=60)
def get_sessions_production(centre_id=None, date_debut=None, date_fin=None):
    """Récupérer les sessions de production"""
    try:
        params = {}
        if centre_id:
            params['centre_usinage_id'] = centre_id
        if date_debut:
            params['date_debut'] = date_debut.isoformat()
        if date_fin:
            params['date_fin'] = date_fin.isoformat()
        
        response = requests.get(f"{API_BASE_URL}/sessions-production/", params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API: {e}")
        return []

@st.cache_data(ttl=60)
def get_production_summary():
    """Récupérer le résumé de production"""
    try:
        response = requests.get(f"{API_BASE_URL}/stats/production-summary")
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erreur API: {response.status_code}")
            return {}
    except requests.exceptions.RequestException as e:
        st.error(f"Erreur de connexion à l'API: {e}")
        return {}

def calculate_synthetic_performance_rate(session):
    """Calculer le taux de rendement synthétique (TRS)"""
    # TRS = Taux de disponibilité × Taux de performance × Taux de qualité
    # Pour simplifier, on utilise les données disponibles
    taux_occupation = float(session.get('taux_occupation', 0) or 0)
    taux_attente = float(session.get('taux_attente', 0) or 0)
    taux_arret = float(session.get('taux_arret_volontaire', 0) or 0)
    
    # Taux de disponibilité = 100% - taux d'arrêt
    taux_disponibilite = 100 - taux_arret
    
    # Taux de performance basé sur l'occupation
    taux_performance = taux_occupation
    
    # Taux de qualité (assumé à 95% par défaut, pourrait être calculé avec plus de données)
    taux_qualite = 95.0
    
    # TRS = (Disponibilité × Performance × Qualité) / 10000
    trs = (taux_disponibilite * taux_performance * taux_qualite) / 10000
    
    return {
        'trs': round(trs, 2),
        'taux_disponibilite': round(taux_disponibilite, 2),
        'taux_performance': round(taux_performance, 2),
        'taux_qualite': round(taux_qualite, 2)
    }

def main():
    st.title("🏭 Dashboard Production Industrielle - Taux de Rendement Synthétique")
    st.markdown("---")
    
    # Sidebar pour les filtres
    st.sidebar.header("🔧 Filtres")
    
    # Récupérer les centres d'usinage
    centres = get_centres_usinage()
    
    if not centres:
        st.error("Impossible de récupérer les données des centres d'usinage. Vérifiez que l'API est accessible.")
        return
    
    # Filtre par type de centre d'usinage
    types_cu = list(set([centre['type_cu'] for centre in centres if centre.get('type_cu')]))
    types_cu.sort()
    
    type_cu_options = ["Tous"] + types_cu
    selected_type_cu = st.sidebar.selectbox(
        "Type de centre d'usinage",
        options=type_cu_options
    )
    
    # Filtrer les centres par type sélectionné
    if selected_type_cu == "Tous":
        centres_filtres = centres
    else:
        centres_filtres = [c for c in centres if c.get('type_cu') == selected_type_cu]
    
    # Filtres de date
    col1, col2 = st.sidebar.columns(2)
    with col1:
        date_debut = st.date_input(
            "Date début",
            value=date.today() - timedelta(days=30),
            max_value=date.today()
        )
    with col2:
        date_fin = st.date_input(
            "Date fin",
            value=date.today(),
            max_value=date.today()
        )
    
    # Section 1: Vue d'ensemble des centres d'usinage par type
    st.header("📊 Vue d'ensemble des centres d'usinage")
    
    if centres_filtres:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total centres", len(centres_filtres))
        
        centres_actifs = [c for c in centres_filtres if c.get('actif', True)]
        with col2:
            st.metric("Centres actifs", len(centres_actifs))
        
        with col3:
            types_uniques = len(set([c['type_cu'] for c in centres_filtres if c.get('type_cu')]))
            st.metric("Types de CU", types_uniques)
        
        # Affichage des centres sous forme de tableau
        df_centres = pd.DataFrame(centres_filtres)
        if not df_centres.empty:
            st.subheader(f"Liste des centres d'usinage - Type: {selected_type_cu}")
            st.dataframe(
                df_centres[['nom', 'type_cu', 'description', 'actif']].rename(columns={
                    'nom': 'Nom',
                    'type_cu': 'Type',
                    'description': 'Description',
                    'actif': 'Actif'
                }),
                use_container_width=True
            )
    
    # Section 2: Sessions de production et TRS
    st.header("🔄 Sessions de production et Taux de Rendement Synthétique")
    
    # Récupérer toutes les sessions pour les centres filtrés
    all_sessions = []
    for centre in centres_filtres:
        sessions = get_sessions_production(centre['id'], date_debut, date_fin)
        all_sessions.extend(sessions)
    
    if all_sessions:
        # Calculer les TRS pour chaque session
        sessions_with_trs = []
        for session in all_sessions:
            trs_data = calculate_synthetic_performance_rate(session)
            session_enhanced = session.copy()
            session_enhanced.update(trs_data)
            sessions_with_trs.append(session_enhanced)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total sessions", len(sessions_with_trs))
        
        with col2:
            total_pieces = sum(session.get('total_pieces', 0) for session in sessions_with_trs)
            st.metric("Total pièces", total_pieces)
        
        with col3:
            avg_trs = sum(session.get('trs', 0) for session in sessions_with_trs) / len(sessions_with_trs) if sessions_with_trs else 0
            st.metric("TRS moyen", f"{avg_trs:.1f}%")
        
        with col4:
            avg_disponibilite = sum(session.get('taux_disponibilite', 0) for session in sessions_with_trs) / len(sessions_with_trs) if sessions_with_trs else 0
            st.metric("Disponibilité moyenne", f"{avg_disponibilite:.1f}%")
        
        # Graphiques TRS
        if len(sessions_with_trs) > 0:
            df_sessions = pd.DataFrame(sessions_with_trs)
            
            # Mapper les IDs des centres aux noms et types
            centre_map = {centre['id']: {'nom': centre['nom'], 'type_cu': centre['type_cu']} for centre in centres}
            df_sessions['centre_nom'] = df_sessions['centre_usinage_id'].map(lambda x: centre_map.get(x, {}).get('nom', 'Inconnu'))
            df_sessions['centre_type'] = df_sessions['centre_usinage_id'].map(lambda x: centre_map.get(x, {}).get('type_cu', 'Inconnu'))
            
            # Convertir les colonnes numériques pour éviter les erreurs d'agrégation
            numeric_cols = ['trs', 'taux_disponibilite', 'taux_performance', 'taux_qualite']
            for col in numeric_cols:
                if col in df_sessions.columns:
                    df_sessions[col] = pd.to_numeric(df_sessions[col], errors='coerce').fillna(0)
            
            # Graphique TRS par type de centre
            try:
                # Vérifier que les colonnes nécessaires existent
                required_cols = ['centre_type', 'trs', 'taux_disponibilite', 'taux_performance', 'taux_qualite']
                available_cols = [col for col in required_cols if col in df_sessions.columns]
                
                if 'centre_type' in available_cols and 'trs' in available_cols:
                    agg_dict = {}
                    for col in ['trs', 'taux_disponibilite', 'taux_performance', 'taux_qualite']:
                        if col in df_sessions.columns:
                            agg_dict[col] = 'mean'
                    
                    trs_par_type = df_sessions.groupby('centre_type').agg(agg_dict).reset_index()
                    
                    if not trs_par_type.empty and 'trs' in trs_par_type.columns:
                        fig_trs = px.bar(
                            trs_par_type,
                            x='centre_type',
                            y='trs',
                            title='Taux de Rendement Synthétique (TRS) par type de centre d\'usinage',
                            labels={'centre_type': 'Type de centre', 'trs': 'TRS (%)'},
                            color='trs',
                            color_continuous_scale='RdYlGn'
                        )
                        fig_trs.update_layout(showlegend=False)
                        st.plotly_chart(fig_trs, use_container_width=True)
                    
                    # Graphique de décomposition du TRS
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Graphique radar pour les composants du TRS
                        radar_cols = ['taux_disponibilite', 'taux_performance', 'taux_qualite']
                        available_radar_cols = [col for col in radar_cols if col in trs_par_type.columns]
                        
                        if len(available_radar_cols) >= 2 and not trs_par_type.empty:
                            fig_radar = go.Figure()
                            
                            for _, row in trs_par_type.iterrows():
                                values = [row.get(col, 0) for col in available_radar_cols]
                                labels = [col.replace('taux_', '').title() for col in available_radar_cols]
                                
                                fig_radar.add_trace(go.Scatterpolar(
                                    r=values,
                                    theta=labels,
                                    fill='toself',
                                    name=row['centre_type']
                                ))
                            
                            fig_radar.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100]
                                    )),
                                showlegend=True,
                                title="Décomposition du TRS par type de centre"
                            )
                            st.plotly_chart(fig_radar, use_container_width=True)
                        else:
                            st.info("Données insuffisantes pour le graphique radar.")
                    
                    with col2:
                        # Graphique temporel du TRS
                        if 'date_production' in df_sessions.columns and 'trs' in df_sessions.columns:
                            try:
                                df_sessions['date_production'] = pd.to_datetime(df_sessions['date_production'], errors='coerce')
                                df_sessions_clean = df_sessions.dropna(subset=['date_production', 'trs'])
                                
                                if not df_sessions_clean.empty:
                                    trs_temporel = df_sessions_clean.groupby(['date_production', 'centre_type'])['trs'].mean().reset_index()
                                    
                                    if not trs_temporel.empty:
                                        fig_timeline = px.line(
                                            trs_temporel,
                                            x='date_production',
                                            y='trs',
                                            color='centre_type',
                                            title='Évolution du TRS par jour et type de centre',
                                            labels={'date_production': 'Date', 'trs': 'TRS (%)', 'centre_type': 'Type de centre'}
                                        )
                                        st.plotly_chart(fig_timeline, use_container_width=True)
                                    else:
                                        st.info("Aucune donnée temporelle disponible pour le TRS.")
                                else:
                                    st.info("Données de date invalides pour le graphique temporel.")
                            except Exception as e:
                                st.warning(f"Erreur lors de la création du graphique temporel : {str(e)}")
                        else:
                            st.info("Colonnes date_production ou trs manquantes pour le graphique temporel.")
                
                else:
                    st.warning("Colonnes nécessaires manquantes pour les graphiques TRS.")
                
            except Exception as e:
                st.error(f"Erreur lors de la création des graphiques TRS : {str(e)}")
                st.info("Données disponibles :")
                if not df_sessions.empty:
                    st.write("Colonnes disponibles :", list(df_sessions.columns))
                    st.dataframe(df_sessions.head(), use_container_width=True)
            
            # Tableau détaillé des sessions avec TRS
            st.subheader("Détail des sessions avec TRS")
            
            # Préparer les données pour l'affichage
            display_columns = ['date_production', 'centre_nom', 'centre_type', 'total_pieces', 'trs', 'taux_disponibilite', 'taux_performance']
            available_columns = [col for col in display_columns if col in df_sessions.columns]
            
            if available_columns:
                df_display = df_sessions[available_columns].copy()
                
                # Renommer les colonnes pour l'affichage
                column_names = {
                    'date_production': 'Date',
                    'centre_nom': 'Centre',
                    'centre_type': 'Type',
                    'total_pieces': 'Pièces',
                    'trs': 'TRS (%)',
                    'taux_disponibilite': 'Disponibilité (%)',
                    'taux_performance': 'Performance (%)'
                }
                
                df_display = df_display.rename(columns={k: v for k, v in column_names.items() if k in df_display.columns})
                
                # Trier par TRS décroissant
                if 'TRS (%)' in df_display.columns:
                    df_display = df_display.sort_values('TRS (%)', ascending=False)
                
                st.dataframe(df_display, use_container_width=True)
    else:
        st.info("Aucune session de production trouvée pour les critères sélectionnés.")
    
    # Section 3: Analyse comparative par type de CU
    st.header("📈 Analyse comparative par type de centre d'usinage")
    
    if all_sessions:
        # Statistiques par type de CU
        df_sessions = pd.DataFrame(sessions_with_trs)
        centre_map = {centre['id']: {'nom': centre['nom'], 'type_cu': centre['type_cu']} for centre in centres}
        df_sessions['centre_type'] = df_sessions['centre_usinage_id'].map(lambda x: centre_map.get(x, {}).get('type_cu', 'Inconnu'))
        
        # Convertir les colonnes numériques et gérer les valeurs manquantes
        numeric_columns = ['total_pieces', 'trs', 'taux_disponibilite', 'taux_performance', 'taux_occupation', 'taux_attente']
        for col in numeric_columns:
            if col in df_sessions.columns:
                df_sessions[col] = pd.to_numeric(df_sessions[col], errors='coerce').fillna(0)
        
        # Filtrer les colonnes qui existent réellement dans le DataFrame
        available_numeric_columns = [col for col in numeric_columns if col in df_sessions.columns]
        
        if available_numeric_columns and not df_sessions.empty:
            try:
                # Créer le dictionnaire d'agrégation seulement avec les colonnes disponibles
                agg_dict = {}
                for col in available_numeric_columns:
                    if col == 'total_pieces':
                        agg_dict[col] = 'sum'
                    else:
                        agg_dict[col] = 'mean'
                
                stats_par_type = df_sessions.groupby('centre_type').agg(agg_dict).round(2).reset_index()
                
                if not stats_par_type.empty:
                    st.subheader("Statistiques par type de centre d'usinage")
                    
                    # Créer le dictionnaire de renommage seulement pour les colonnes disponibles
                    rename_dict = {
                        'centre_type': 'Type de centre',
                        'total_pieces': 'Total pièces',
                        'trs': 'TRS moyen (%)',
                        'taux_disponibilite': 'Disponibilité (%)',
                        'taux_performance': 'Performance (%)',
                        'taux_occupation': 'Occupation (%)',
                        'taux_attente': 'Attente (%)'
                    }
                    
                    # Filtrer le dictionnaire de renommage pour les colonnes existantes
                    available_rename_dict = {k: v for k, v in rename_dict.items() if k in stats_par_type.columns}
                    stats_display = stats_par_type.rename(columns=available_rename_dict)
                    
                    st.dataframe(stats_display, use_container_width=True)
                    
                    # Graphique comparatif avec les colonnes disponibles
                    comparison_columns = [col for col in ['trs', 'taux_disponibilite', 'taux_performance'] if col in stats_par_type.columns]
                    
                    if comparison_columns and len(comparison_columns) > 0:
                        fig_comparison = px.bar(
                            stats_par_type,
                            x='centre_type',
                            y=comparison_columns,
                            title='Comparaison des indicateurs de performance par type de centre',
                            labels={'value': 'Pourcentage (%)', 'centre_type': 'Type de centre'},
                            barmode='group'
                        )
                        st.plotly_chart(fig_comparison, use_container_width=True)
                    else:
                        st.info("Données insuffisantes pour afficher le graphique comparatif.")
                        
            except Exception as e:
                st.error(f"Erreur lors du calcul des statistiques : {str(e)}")
                st.info("Affichage des données brutes disponibles :")
                if not df_sessions.empty:
                    st.dataframe(df_sessions.head(), use_container_width=True)
        else:
            st.info("Aucune donnée numérique disponible pour l'analyse comparative.")
    
    # Footer
    st.markdown("---")
    st.markdown("*Dashboard TRS mis à jour automatiquement - Données en cache pendant 1 minute*")
    st.markdown("**TRS = Taux de Disponibilité × Taux de Performance × Taux de Qualité**")

if __name__ == "__main__":
    main() 