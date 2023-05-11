from django.shortcuts import get_list_or_404, get_object_or_404
from django.contrib.auth import get_user, get_user_model
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.conf import settings
from django.db.models import Q, Avg, Count, Prefetch
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework import status
from rest_framework import generics
from rest_framework import filters
from .serializers import ProductSerializer, RecentReleaseSerializers
from .models import kicks, productImg
from google_images_download import google_images_download
from assets.brand_list import brand_list
from django_filters import rest_framework as filters
from reviews.models import Review
import re

User = get_user_model()


class ProductPagination(CursorPagination):
    page_size = 20
    page_size_query_param = None
    max_page_size = 20
    ordering = '-releaseDate'


class ProductFilter(filters.FilterSet):
    search = filters.CharFilter(method='search_filter', label='Search')
    brand = filters.CharFilter(method='brand_filter', lookup_expr='icontains')
    category = filters.CharFilter(field_name='category', lookup_expr='icontains')
    release_date = filters.CharFilter(method='release_date_filter', label='Release Date Range')
    info_registrequired = filters.CharFilter(method='info_registrequired_filter', label='Info_Regist_Required')
    main_page = filters.CharFilter(method='main_page_filter', label='Main_Page_Filter')

    class Meta:
        model = kicks
        fields = ('search', 'brand', 'category', 'release_date', 'info_registrequired', 'main_page')

    def main_page_filter(self, queryset, name, value):
        print('main_page_filter')
        if value == 'most_viewed':
            print('most_viewed')
            ProductPagination.ordering = '-click'

            return queryset


    def search_filter(self, queryset, name, value):
        keyword = value.replace('+', ' ')
        keyword_regex = re.sub(r'\s+', r'\\s*', keyword)

        # Add space between the letters in the keyword if they are not already separated by space
        keyword_with_space = re.sub(r'(?<=\D)(?=\d)|(?<=\d)(?=\D)', ' ', keyword)

        return queryset.filter(
            Q(name__icontains=keyword) |
            Q(name__iregex=fr'{keyword_regex}') |
            Q(name__icontains=keyword_with_space))

    def brand_filter(self, queryset, name, value):
        brand_list = value.split(',')
        q = Q()
        for brand in brand_list:
            q.add(Q(brand__icontains=brand), Q.OR)

        queryset = queryset.filter(q)

        return queryset

    def release_date_filter(self, queryset, name, value):
        if not value:
            return queryset.order_by('-releaseDate')
        else:
            date_range = value.split(',')
            if len(date_range) == 1:
                start_date = end_date = date_range[0]
            else:
                start_date = date_range[0]
                end_date = date_range[1]
        return queryset.filter(releaseDate__range=[start_date, end_date])

    def info_registrequired_filter(self, queryset, name, value):
        if value == 'true':
            return queryset.filter(
                Q(local_imageUrl__icontains='media/images/defaultImg.png') |
                Q(brand__isnull=True) |
                Q(category__isnull=True) |
                Q(releaseDate__isnull=True) |
                Q(retailPrice__isnull=True) |
                Q(colorway__isnull=True) |
                Q(releaseDate__icontains='1900-01-01')
            ).order_by('-releaseDate')
        else:
            return queryset.order_by('-releaseDate')


class ProductListViewSet(generics.ListAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    queryset = kicks.objects.prefetch_related('reviews',
                                              'like_users').annotate(review_count=Count('reviews'),
                                                                     like_count=Count('like_users'),
                                                                     rating_avg=Avg('reviews__rating'))
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter


'''
for main page component
'''


@api_view(['GET'])
@permission_classes([AllowAny])
def recent_releases(request):
    if request.method == 'GET':
        product_list = kicks.objects.exclude(
            local_imageUrl='media/images/defaultImg.png'
        ).exclude(releaseDate__isnull=True).order_by('-releaseDate')[:15]

        serializer = RecentReleaseSerializers(product_list, many=True)
        return Response(serializer.data)
    else:
        return HttpResponse(status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_detail(request, prd_id):
    kick = kicks.objects.prefetch_related('reviews',
                                          'like_users').annotate(review_count=Count('reviews'),
                                                                 like_count=Count('like_users'),
                                                                 rating_avg=Avg('reviews__rating')).get(pk=prd_id)

    # 조회수 증가
    kick.click += 1
    kick.save()
    serializer = ProductSerializer(kick)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def product_like(request, product_id, user_id):
    user = User.objects.get(pk=user_id)
    kick = kicks.objects.get(id=product_id)

    if kick.like_users.filter(id=user_id).exists():
        kick.like_users.remove(user)
        return JsonResponse({'message': 'removed'}, status=status.HTTP_200_OK)
    else:
        kick.like_users.add(user)
        return JsonResponse({'message': 'added'}, status=status.HTTP_200_OK)


