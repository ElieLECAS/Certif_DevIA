class LoginView(TemplateView):
    template_name = 'pages/login.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LoginForm()
        return context
        
    def post(self, request, *args, **kwargs):
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Connexion réussie !')
            
            # Vérifier si l'utilisateur est un client
            try:
                client_user = ClientUser.objects.get(user=user)
                if client_user.is_client_only:
                    return redirect('client_home')
            except ClientUser.DoesNotExist:
                pass
            
        else:
            messages.error(request, 'Identifiants invalides.')
            return render(request, self.template_name, {'form': form})

class LogoutView(View):
    def dispatch(self, request, *args, **kwargs):
        # Effacer tous les messages précédents
        storage = messages.get_messages(request)
        storage.used = True
        
        logout(request)
        messages.info(request, 'Vous avez été déconnecté.')
        return redirect('login')
    

class ConversationListView(LoginRequiredMixin, ExpeditionOnlyMixin, CentreUsinageOnlyMixin, GroupRequiredMixin, TemplateView):
    template_name = 'pages/conversations_list.html'


    def dispatch(self, request, *args, **kwargs):
        # Si l'utilisateur est un client, le rediriger vers la page d'accueil client
        if not (request.user.is_staff or request.user.is_superuser):
            try:
                ClientUser.objects.get(user=request.user)
                return redirect('client_home')
            except ClientUser.DoesNotExist:
                pass
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Filtrer par statut si spécifié
        status_filter = self.request.GET.get('status', None)
        
        # Utiliser le cache pour les conversations
        from django.core.cache import cache
        cache_key = f'conversations_list_{status_filter}' if status_filter else 'conversations_list_all'
        
        conversations = cache.get(cache_key)
        if conversations is None:
            # Récupérer toutes les conversations
            conversations = Conversation.objects.all()
            
            # Appliquer le filtre si nécessaire
            if status_filter:
                conversations = conversations.filter(status=status_filter)
            
            # Ordonner par date de mise à jour décroissante
            conversations = conversations.order_by('-updated_at')
            
            # Mettre en cache pour 5 minutes (300 secondes)
            cache.set(cache_key, conversations, 300)
        
        context['conversations'] = conversations
        context['status_filter'] = status_filter
        context['count'] = conversations.count()
        
        return context

class ConversationDetailView(LoginRequiredMixin, ExpeditionOnlyMixin, CentreUsinageOnlyMixin, GroupRequiredMixin, TemplateView):
    template_name = 'pages/conversation_detail.html'


    def dispatch(self, request, *args, **kwargs):
        # Vérifier que l'utilisateur a le droit d'accéder à cette conversation
        conversation_id = kwargs.get('conversation_id')
        
        try:
            conversation = Conversation.objects.get(id=conversation_id)
            
            # Si l'utilisateur est un client, vérifier qu'il est le propriétaire de la conversation
            if not (request.user.is_staff or request.user.is_superuser):
                try:
                    client_user = ClientUser.objects.get(user=request.user)
                    if client_user.is_client_only:
                        # Vérifier si l'utilisateur est le propriétaire de la conversation
                        if conversation.user != request.user:
                            # Si l'ancien lien n'existe pas, vérifier par le nom d'utilisateur
                            if not (conversation.client_name and request.user.username in conversation.client_name):
                                messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette conversation.")
                                return redirect('client_home')
                except ClientUser.DoesNotExist:
                    pass
                    
        except Conversation.DoesNotExist:
            # Si la conversation n'existe pas, rediriger vers la liste des conversations
            if request.user.is_staff or request.user.is_superuser:
                return redirect('conversations_list')
            else:
                return redirect('client_home')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer l'ID de la conversation
        conversation_id = kwargs.get('conversation_id')
        
        # Utiliser le cache pour les détails de la conversation
        from django.core.cache import cache
        cache_key = f'conversation_detail_{conversation_id}'
        
        conversation_data = cache.get(cache_key)
        if conversation_data is None:
            try:
                # Récupérer la conversation
                conversation = Conversation.objects.get(id=conversation_id)
                
                # Extraire uniquement les messages utilisateur et assistant (pas les messages système)
                messages_list = []
                if conversation.history:
                    messages_list = [msg for msg in conversation.history if msg.get('role') != 'system']
                
                # Stocker les données nécessaires
                conversation_data = {
                    'conversation': conversation,
                    'messages': messages_list
                }
                
                # Mettre en cache pour 5 minutes (300 secondes)
                cache.set(cache_key, conversation_data, 300)
                
            except Conversation.DoesNotExist:
                conversation_data = {'error': "Conversation non trouvée"}
        
        # Mettre à jour le contexte avec les données
        context.update(conversation_data)
        
        # Déterminer si l'utilisateur est un admin pour le bouton de retour (ne pas mettre en cache)
        context['is_admin'] = self.request.user.is_staff or self.request.user.is_superuser
        
        return context

class ClientRegisterView(ExpeditionOnlyMixin, CentreUsinageOnlyMixin, GroupRequiredMixin, TemplateView):
    template_name = 'pages/client_register.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ClientRegistrationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = ClientRegistrationForm(data=request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Compte créé avec succès ! Vous pouvez maintenant vous connecter.')
            return redirect('login')
        else:
            return render(request, self.template_name, {'form': form})

class OpenaiView(LoginRequiredMixin, ExpeditionOnlyMixin, CentreUsinageOnlyMixin, GroupRequiredMixin, TemplateView):
    template_name = 'pages/openai_chat.html'

    def dispatch(self, request, *args, **kwargs):
        # Vérifier si l'utilisateur est un client ou un personnel autorisé
        try:
            client_user = ClientUser.objects.get(user=request.user)
            # Les clients peuvent accéder à cette vue
        except ClientUser.DoesNotExist:
            # Si ce n'est pas un client, vérifier s'il a les permissions d'admin
            if not request.user.is_staff and not request.user.is_superuser:
                # Rediriger vers la page d'accueil si l'utilisateur n'est ni client ni admin
                messages.error(request, "Vous n'avez pas les permissions nécessaires pour accéder à cette page.")
                return redirect('login')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        from .langchain_utils import load_all_jsons
        import json
        
        # Récupérer la conversation active
        if self.request.user.is_authenticated:
            try:
                # Récupérer le profil du client s'il existe
                client_user = ClientUser.objects.get(user=self.request.user)
                conversation = client_user.active_conversation
                
                if conversation:
                    context['conversation_id'] = conversation.id
                    context['conversation'] = conversation
                    context['history'] = json.dumps(conversation.history)
                else:
                    context['conversation_id'] = "temp"
                    context['history'] = "[]"
            except ClientUser.DoesNotExist:
                context['conversation_id'] = "temp"
                context['history'] = "[]"
        else:
            context['conversation_id'] = "temp"
            context['history'] = "[]"
        
        # Récupérer les informations du client connecté
        preprompt, client_json, renseignements, retours, commandes = load_all_jsons(user=self.request.user)
        
        # Ajouter les informations du client au contexte pour le template
        context['client_info'] = client_json
        
        return context

    def post(self, request, *args, **kwargs):
        try:
            from .langchain_utils import initialize_faiss, load_all_jsons, get_conversation_history
            from langchain_openai import ChatOpenAI
            from langchain import hub

            data = json.loads(request.body.decode('utf-8'))
            user_input = data.get('message')
            conversation_id = data.get('conversation_id')
            
            if not user_input:
                return JsonResponse({
                    "error": "Le message ne peut pas être vide"
                }, status=400)
            
            # Configuration de l'API key
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if not openai_api_key:
                return JsonResponse({
                    "error": "Clé API OpenAI non configurée"
                }, status=500)
            
            # Récupérer les données contextuelles en passant l'utilisateur connecté
            preprompt, client_json, renseignements, retours, commandes = load_all_jsons(user=request.user)
            
            # Extraire le nom du client depuis le JSON client si disponible
            client_name = "Client"
            if client_json and isinstance(client_json, dict):
                if 'client_informations' in client_json:
                    client_info = client_json['client_informations']
                    nom = client_info.get('nom', '')
                    prenom = client_info.get('prenom', '')
                    if nom and prenom:
                        client_name = f"{prenom} {nom}"
                    elif nom:
                        client_name = nom
            
            # Récupérer ou créer une conversation
            if conversation_id and conversation_id != "temp":
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                except Conversation.DoesNotExist:
                    # Créer une nouvelle conversation car il y a un message
                    conversation = Conversation.objects.create(
                        client_name=client_name,
                        status="nouveau",
                        user=request.user
                    )
            else:
                # Si c'est une conversation temporaire, maintenant qu'il y a un message,
                # on la crée réellement en base de données
                conversation = Conversation.objects.create(
                    client_name=client_name,
                    status="nouveau",
                    user=request.user
                )
            
            # Initialiser LLM
            llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", max_tokens=500, temperature=0.4)
            
            # Initialiser FAISS
            vectorstore = initialize_faiss(openai_api_key)
            
            # Ajouter le message de l'utilisateur à l'historique
            conversation.add_message("user", user_input)
            
            # Récupérer l'historique complet
            conversation_history = conversation.history
            
            # Ajouter les prompts système s'ils n'existent pas déjà
            if len(conversation_history) <= 1:  # Seulement le message utilisateur qu'on vient d'ajouter
                system_prompts = [
                    {"role": "system", "content": preprompt.get("content", "Vous êtes un assistant virtuel serviable et professionnel.")},
                    {"role": "system", "content": json.dumps(client_json)},
                    {"role": "system", "content": json.dumps(retours)},
                    {"role": "system", "content": json.dumps(commandes)}
                ]
                # Insérer au début de l'historique
                conversation.history = system_prompts + conversation_history
                conversation.save()
                conversation_history = conversation.history
            
            # Convertir l'historique de conversation en texte
            history_text = get_conversation_history(conversation_history)
            
            # Faire une recherche sémantique avec FAISS
            faiss_results = vectorstore.similarity_search(user_input)
            
            # Extraire le texte des résultats de FAISS
            faiss_context = "\n".join([doc.page_content for doc in faiss_results])
            
            # Préparer le contexte complet
            complete_context = history_text + "\nContext from FAISS:\n" + faiss_context
            
            # Obtenir la réponse du modèle
            response = llm.invoke(complete_context + "\nUser: " + user_input)
            assistant_response = response.content if hasattr(response, 'content') else "Aucune réponse trouvée."
            
            # Ajouter la réponse à l'historique
            conversation.add_message("assistant", assistant_response)
            
            # Ne plus mettre à jour le statut automatiquement
            # if conversation.status == "nouveau":
            #     conversation.set_status("en_cours")
            
            return JsonResponse({
                "response": assistant_response,
                "conversation_id": conversation.id,
                "history": conversation.history
            })
            
        except Exception as e:
            return JsonResponse({
                "error": "Une erreur est survenue",
                "details": str(e)
            }, status=500)

    @classmethod
    def reset_chat(cls, request, *args, **kwargs):
        if request.method == 'POST':
            # Rediriger vers une nouvelle page sans créer de conversation
            return JsonResponse({
                "status": "success",
                "conversation_id": "temp"
            })
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    def close_conversation(self, request, *args, **kwargs):
        from .langchain_utils import save_conversation_to_csv, load_all_jsons
        
        if request.method == 'POST':
            try:
                data = json.loads(request.body.decode('utf-8'))
                conversation_id = data.get('conversation_id')
                
                # Si c'est une conversation temporaire, pas besoin de clôturer
                if not conversation_id or conversation_id == "temp":
                    return JsonResponse({
                        "status": "success",
                        "message": "Aucune conversation active à clôturer"
                    })
                
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                except Conversation.DoesNotExist:
                    return JsonResponse({
                        "error": "Conversation non trouvée"
                    }, status=404)
                
                # Vérifier si la conversation a un historique réel (au moins un message)
                has_real_messages = False
                if conversation.history:
                    for msg in conversation.history:
                        if msg.get('role') in ['user', 'assistant'] and msg.get('content'):
                            has_real_messages = True
                            break
                
                # Si aucun message réel, supprimer la conversation plutôt que de la clôturer
                if not has_real_messages:
                    conversation.delete()
                    return JsonResponse({
                        "status": "success",
                        "message": "Conversation vide supprimée"
                    })
                
                # Configuration de l'API key
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if not openai_api_key:
                    return JsonResponse({
                        "error": "Clé API OpenAI non configurée"
                    }, status=500)
                
                # Récupérer les informations client avec l'utilisateur connecté
                preprompt, client_json, renseignements, retours, commandes = load_all_jsons(user=request.user)
                
                # Initialiser LLM
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", max_tokens=500, temperature=0.3)
                
                # Convertir l'historique de conversation en texte pour le résumé
                from .langchain_utils import get_conversation_history
                conversation_text = get_conversation_history(conversation.history)
                
                # Générer le résumé
                summary_prompt = f"\n{conversation_text}\n\nGénère un résumé de l'entière de la conversation avec le client pour le transmettre à un technicien SAV humain, donne lui les points importants pour lui permettre de gagner du temps sur la relecture de la conversation SAV."
                summary_response = llm.invoke(summary_prompt)
                summary = summary_response.content if hasattr(summary_response, 'content') else "Résumé indisponible."
                
                # Enregistrer le résumé dans la conversation
                conversation.summary = summary
                # Ne pas changer le statut automatiquement lors de la clôture
                # conversation.status = "termine"
                conversation.save()
                
                # Exporter en CSV si nécessaire
                try:
                    save_conversation_to_csv(conversation.id, summary)
                except:
                    pass  # Ne pas interrompre si l'export CSV échoue
                
                return JsonResponse({
                    "status": "success",
                    "summary": summary
                })
                
            except Exception as e:
                return JsonResponse({
                    "error": "Erreur lors de la clôture de la conversation",
                    "details": str(e)
                }, status=500)
                
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    def upload_images(self, request, *args, **kwargs):
        from .langchain_utils import save_uploaded_file, initialize_faiss, get_conversation_history, load_all_jsons
        
        if request.method == 'POST':
            try:
                # Vérifier s'il y a des images dans la requête
                if 'images' not in request.FILES:
                    return JsonResponse({
                        "error": "Aucune image n'a été téléchargée"
                    }, status=400)
                
                # Récupérer l'ID de conversation
                conversation_id = request.POST.get('conversation_id')
                
                # Configuration de l'API key pour réutilisation
                openai_api_key = os.getenv('OPENAI_API_KEY')
                if not openai_api_key:
                    return JsonResponse({
                        "error": "Clé API OpenAI non configurée"
                    }, status=500)
                
                # Si c'est une conversation temporaire ou qu'il n'y a pas d'ID, créer une vraie conversation
                if not conversation_id or conversation_id == "temp":
                    # Récupérer les informations du client
                    preprompt, client_json, renseignements, retours, commandes = load_all_jsons(user=self.request.user)
                    
                    # Extraire le nom du client
                    client_name = "Client"
                    if client_json and isinstance(client_json, dict):
                        if 'client_informations' in client_json:
                            client_info = client_json['client_informations']
                            nom = client_info.get('nom', '')
                            prenom = client_info.get('prenom', '')
                            if nom and prenom:
                                client_name = f"{prenom} {nom}"
                            elif nom:
                                client_name = nom
                    
                    # Créer une nouvelle conversation car des images sont envoyées
                    conversation = Conversation.objects.create(client_name=client_name, status="nouveau")
                else:
                    try:
                        conversation = Conversation.objects.get(id=conversation_id)
                    except Conversation.DoesNotExist:
                        return JsonResponse({
                            "error": "Conversation non trouvée"
                        }, status=404)
                
                # Récupérer les images
                images = request.FILES.getlist('images')
                
                # Sauvegarder les images et récupérer les chemins
                image_paths = []
                for image in images:
                    path = save_uploaded_file(image)
                    image_paths.append(path)
                    # Ajouter l'image à l'historique
                    conversation.add_message(
                        "user",
                        f"📤 Image envoyée: {os.path.basename(path)}",
                        image_path=path
                    )
                
                # Initialiser LLM
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(api_key=openai_api_key, model="gpt-4o-mini", max_tokens=500, temperature=0.4)
                
                # Initialiser FAISS
                vectorstore = initialize_faiss(openai_api_key)
                
                # Convertir l'historique en texte
                history_text = get_conversation_history(conversation.history)
                
                # Faire une recherche sémantique avec FAISS pour le contexte sur les photos
                faiss_results = vectorstore.similarity_search("Photos envoyées pour SAV")
                
                # Extraire le texte des résultats de FAISS
                faiss_context = "\n".join([doc.page_content for doc in faiss_results])
                
                # Préparer le contexte complet avec une demande d'analyse d'images
                complete_context = (
                    f"{history_text}\n"
                    "Context from FAISS:\n"
                    f"{faiss_context}\n"
                    "User: Des photos ont été envoyées. Veuillez les analyser et donner des premiers conseils au client."
                )
                
                # Obtenir la réponse du modèle
                response = llm.invoke(complete_context)
                assistant_response = response.content if hasattr(response, 'content') else "J'ai bien reçu vos images. Comment puis-je vous aider avec ces photos ?"
                
                # Ajouter la réponse à l'historique
                conversation.add_message("assistant", assistant_response)
                
                # Ne plus mettre à jour le statut automatiquement
                # if conversation.status == "nouveau":
                #     conversation.set_status("en_cours")
                
                return JsonResponse({
                    "response": assistant_response,
                    "conversation_id": conversation.id,
                    "history": conversation.history
                })
                
            except Exception as e:
                return JsonResponse({
                    "error": "Erreur lors du traitement des images",
                    "details": str(e)
                }, status=500)
                
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)

    def update_client_name(self, request, *args, **kwargs):
        if request.method == 'POST':
            try:
                data = json.loads(request.body.decode('utf-8'))
                conversation_id = data.get('conversation_id')
                client_name = data.get('client_name')
                
                if not conversation_id or not client_name:
                    return JsonResponse({
                        "error": "ID de conversation ou nom du client manquant"
                    }, status=400)
                
                try:
                    conversation = Conversation.objects.get(id=conversation_id)
                except Conversation.DoesNotExist:
                    return JsonResponse({
                        "error": "Conversation non trouvée"
                    }, status=404)
                
                # Mettre à jour le nom du client
                conversation.client_name = client_name
                conversation.save()
                
                return JsonResponse({
                    "status": "success",
                    "message": "Nom du client mis à jour avec succès"
                })
                
            except Exception as e:
                return JsonResponse({
                    "error": "Erreur lors de la mise à jour du nom du client",
                    "details": str(e)
                }, status=500)
                
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)