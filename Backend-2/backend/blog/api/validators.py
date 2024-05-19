from django.core.exceptions import ValidationError


def validate_ingredients(self, attrs):
        ingredients = self.initial_data.get('ingredients')
        list = []
        for i in ingredients:
            amount = i['amount']
            if not amount:
                raise ValidationError(
                    'Количество ингридиентов не может быть меньше 0'
                )
            if i['id'] in list:
                raise ValidationError(
                    'Ингридиенты не должны повторяться.'
                )
            list.append(i['id'])
        return attrs
