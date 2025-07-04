from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from selenium.common.exceptions import TimeoutException

from accounts.decorators import sign_in_required
from webscraper.services.webscraper.math.math import MathWebscraper

from .services.webscraper.bulgarian import BulgarianWebscraper
# from backend.webscraper.services.webscraper.bulgarian import BulgarianWebscraper
from .services.webscraper.math.matematikabg import MatematikaBGWebscraper
from .services.chatbot import ChatBot
from .models import Question, Article
from .serializers import ArticleSerializer, QuestionSerializer

from rest_framework.permissions import AllowAny, IsAuthenticated

@api_view(['GET'])
# @sign_in_required
# @permission_classes([IsAuthenticated])
def scrape(request, category, query):
    if not query or not category:
        return JsonResponse({'error': 'No category or query provided'}, status=400)
    
    match category:
        case 'math':
            return Response({"error": "Not implemented yet"}, status=501)
            webscraper = MathWebscraper()
        case 'bg':
            webscraper = BulgarianWebscraper()
        case _:
            return JsonResponse({'error': 'Invalid category'}, status=400)
        
    user = request.user
    question = Question.objects.create(
        question=query,
        category=category,
        user=user
    )
    
    question.save()
    
    print('Scraping data...')
    try:
        raw_data = webscraper.search(query)
    except TimeoutException:
        return Response({"error": "Request timed out"}, status=500)
    
    relevant_results = []
    
    print('Scraper data collected')
    # print(raw_data)
    
    chatbot = ChatBot()

    for url, article_text in raw_data.items():
        print('Sending data to AI...')
        ai_response = chatbot.process_data(query, category, article_text)
        
        # print(ai_response)
        
        if "Текстът не съдържа информация" not in ai_response:
            relevant_results.append({
                "url": url,
                "text": ai_response
            })
            
            article = Article(
                question=question,
                url=url,
                text=ai_response,
            )
            article.save() 
    
        print('Data collected')  
        
    if len(relevant_results) < 1:
        print("No relevant results found, generating text...")
        url="https://gemini.google.com/"
        ai_response = chatbot.generate_text(query, category)
        article = Article(
            question=question,
            url=url,
            text=ai_response
        ) 
        article.save()
        
        relevant_results.append({
            "url": url,
            "text": ai_response
        })
        
    return Response({"results": relevant_results, "question": QuestionSerializer(question).data}, status=200)


@api_view(['GET'])
@sign_in_required
@permission_classes([IsAuthenticated])
def get_questions(request):
    user = request.user
    
    questions = Question.objects.filter(user=user).order_by('-created_at')
    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data, status=200)

@api_view(['GET'])
@sign_in_required
@permission_classes([IsAuthenticated])
def get_articles_by_question(request, question_id):
    question = Question.objects.get(id=question_id)
    
    if question.user != request.user:
        return Response({"You don't have access to this data!"}, status=403)
    
    articles = Article.objects.filter(question=question).order_by('-created_at')
    
    article_serializer = ArticleSerializer(articles, many=True)
    question_serializer = QuestionSerializer(question)
    
    return Response({
        "articles": article_serializer.data,
        "question": question_serializer.data
    }, status=200)