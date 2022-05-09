import djoser.serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.settings import api_settings

from api.fields import ImageBase64Field
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientRecipeRelation,
    Recipe,
    ShoppingCart,
    Subscription,
    Tag,
)

User = get_user_model()


class CustomUserCreateSerializer(djoser.serializers.UserCreateSerializer):
    id = serializers.PrimaryKeyRelatedField(
        required=False, queryset=User.objects.all())

    class Meta:
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'password')
        model = User


class AuthorSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False

        return Subscription.objects.filter(
            author=obj, user=self.context['request'].user).exists()

    class Meta:
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name',
            'is_subscribed')
        model = User


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        fields = '__all__'
        model = Tag


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'name', 'measurement_unit')
        model = Ingredient


class IngredientRecipeRelationSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all())
    name = serializers.StringRelatedField(source='ingredient.name')
    measurement_unit = serializers.StringRelatedField(
        source='ingredient.measurement_unit')

    class Meta:
        fields = ('id', 'name', 'measurement_unit', 'amount')
        model = IngredientRecipeRelation


class RecipeSerializerList(serializers.ModelSerializer):
    author = AuthorSerializer(required=False, many=False, read_only=True)
    tags = TagSerializer(required=False, many=True, read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def __is_recipe(self, obj, model):
        if not self.context['request'].user.is_authenticated:
            return False

        return model.objects.filter(
            recipe=obj, user=self.context['request'].user).exists()

    def get_is_in_shopping_cart(self, obj):
        return self.__is_recipe(obj, ShoppingCart)

    def get_is_favorited(self, obj):
        return self.__is_recipe(obj, Favorite)

    def get_ingredients(self, obj):
        return IngredientRecipeRelationSerializer(
            IngredientRecipeRelation.objects.filter(recipe=obj).all(),
            many=True).data

    class Meta:
        exclude = ('created', )
        model = Recipe


class RecipeCreateIngredientSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient', queryset=Ingredient.objects.all())

    class Meta:
        fields = ('id', 'amount')
        model = IngredientRecipeRelation


class CustomUserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    def get_is_subscribed(self, obj):
        if 'request' not in self.context:
            return False

        if not self.context['request'].user.is_authenticated:
            return False

        return Subscription.objects.filter(
            author=obj, user=self.context['request'].user).exists()

    class Meta:
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed')
        model = User


class RecipeShortSerilizer(serializers.ModelSerializer):
    class Meta:
        fields = ('id', 'image', 'name', 'cooking_time')
        model = Recipe


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = RecipeCreateIngredientSerializer(many=True)
    image = ImageBase64Field()
    author = CustomUserSerializer(required=False)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    def __is_recipe(self, obj, model):
        if not self.context['request'].user.is_authenticated:
            return False

        return model.objects.filter(
            recipe=obj, user=self.context['request'].user).exists()

    def get_is_in_shopping_cart(self, obj):
        return self.__is_recipe(obj, ShoppingCart)

    def get_is_favorited(self, obj):
        return self.__is_recipe(obj, Favorite)

    def validate(self, data):
        method = self.context.get('request').method
        author = self.context.get('request').user
        recipe_name = data.get('name')
        ingredients = data.get('ingredients')
        tags = self.initial_data.get('tags')

        if method in ('POST', 'PUT'):
            if (method == 'POST'
                and Recipe.objects.filter(author=author,
                                          name=recipe_name).exists()):
                raise serializers.ValidationError(
                    'Такой рецепт у вас уже есть!'
                )
            self.ingr_validate(ingredients)
            self.tag_validate(tags)

            if method == 'POST':
                data['author'] = author
            data['ingredients'] = ingredients
            data['tags'] = tags

        if method == 'PATCH':
            if ingredients:
                self.ingr_validate(ingredients)
                data['ingredients'] = ingredients
            if tags:
                self.tag_validate(tags)
                data['tags'] = tags
        return data

    def ingr_validate(self, ingredients):
        ingrs_set = set()
        if not ingredients:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один ингридиент'
            )
        for ingredient in ingredients:
            amount = ingredient.get('amount')
            ingr_id = ingredient.get('id')
            if ingr_id in ingrs_set:
                raise serializers.ValidationError(
                    'Ингредиент в рецепте не должен повторяться.'
                )
            try:
                int(amount)
            except ValueError:
                raise serializers.ValidationError(
                    'Количество ингридиента должно быть числом'
                )
            if int(amount) < 1:
                raise serializers.ValidationError(
                    'Убедитесь, что значение количества '
                    'ингредиента больше единицы'
                )
            ingrs_set.add(ingr_id)

    def tag_validate(self, tags):
        if not tags:
            raise serializers.ValidationError(
                'Необходимо добавить хотя бы один тэг'
            )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        obj = Recipe.objects.create(**validated_data)

        obj.tags.set(tags)

        for ingredient in ingredients:
            IngredientRecipeRelation.objects.create(
                recipe=obj, ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ).save()

        return obj

    @ transaction.atomic
    def update(self, instance, validated_data):
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')

        super().update(instance, validated_data)

        instance.tags.set(tags)
        instance.image = validated_data.get('image', instance.image)

        instance.ingredients.clear()
        for ingredient in ingredients:
            IngredientRecipeRelation.objects.create(
                recipe=instance, ingredient=ingredient['ingredient'],
                amount=ingredient['amount']
            ).save()

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        self.fields.pop('ingredients')
        self.fields['tags'] = TagSerializer(many=True)

        representation = super().to_representation(instance)

        representation['ingredients'] = IngredientRecipeRelationSerializer(
            IngredientRecipeRelation.objects.filter(
                recipe=instance).all(), many=True).data

        return representation

    class Meta:
        fields = ('id', 'tags', 'author', 'ingredients', 'is_favorited',
                  'is_in_shopping_cart', 'name', 'image', 'text',
                  'cooking_time')
        model = Recipe


class SubscriptionListSerializer(serializers.ModelSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count', read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    def get_recipes(self, obj):
        recipes_limit = int(self.context['request'].GET.get(
            'recipes_limit', api_settings.PAGE_SIZE))

        user = get_object_or_404(User, pk=obj.pk)
        recipes = Recipe.objects.filter(author=user)[:recipes_limit]

        return RecipeShortSerilizer(recipes, many=True).data

    def get_is_subscribed(self, obj):
        if not self.context['request'].user.is_authenticated:
            return False

        return Subscription.objects.filter(
            author=obj, user=self.context['request'].user).exists()

    class Meta:
        fields = ('id', 'email', 'username', 'first_name', 'last_name',
                  'is_subscribed', 'recipes_count', 'recipes')
        model = User
