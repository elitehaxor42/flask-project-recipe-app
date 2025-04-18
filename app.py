import os
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'a_very_secret_key_that_you_should_change')
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

recipes = [
    {
        'name': 'Delicious Lasagna',
        'image': 'lasagna.jpg',
        'ingredients': [
            'Pasta sheets',
            'Tomato sauce',
            'Ricotta cheese',
            'Mozzarella cheese',
            'Ground beef',
            'Mushrooms'
        ],
        'instructions': 'Layer the tomato sauce, cheeses, mushrooms, and ground beef between the pasta sheets. Bake for 30 minutes at 375F.',
        'serving': 'Serves 4-6 people'
    },
    {
        'name': 'Classic American Apple Pie',
        'image': 'apple_pie.jpg',
        'ingredients': [
            '2 refrigerated pie crusts',
            '6-8 medium apples (like Granny Smith, Honeycrisp, or Fuji), peeled, cored, and sliced',
            '3/4 cup granulated sugar',
            '1/4 cup all-purpose flour',
            '1 teaspoon ground cinnamon',
            '1/4 teaspoon ground nutmeg',
            '1/8 teaspoon ground allspice (optional)',
            '1 tablespoon lemon juice',
            '2 tablespoons unsalted butter, cut into small pieces',
            '1 large egg, beaten (for egg wash)'
        ],
        'instructions': '1. Preheat oven to 425°F (220°C). Place one pie crust in a 9-inch pie plate. Trim excess crust.\n2. In a large bowl, gently mix sliced apples, sugar, flour, cinnamon, nutmeg, allspice (if using), and lemon juice.\n3. Pour the apple mixture into the pie crust. Dot with butter pieces.\n4. Top with the second pie crust. Crimp edges to seal. Cut vents in the top crust.\n5. Brush the top crust with the beaten egg.\n6. Bake for 15 minutes at 425°F. Reduce oven temperature to 375°F (190°C) and bake for another 35-45 minutes, or until the crust is golden brown and the filling is bubbly.\n7. Let cool on a wire rack for at least 2-3 hours before slicing to allow the filling to set.',
        'serving': 'Serves 8'
    }
]


@app.route('/')
def home():
    return render_template('index.html', page_title='My Awesome Recipe Site')

@app.route('/recipes', methods=['GET', 'POST'])
def recipes_page():
    session.setdefault('errors', {})
    session.setdefault('form_data', {})

    if request.method == 'POST':
        errors = {}
        form_data = request.form.to_dict()
        uploaded_file = request.files.get('image')

        required_fields = ['name', 'ingredients', 'instructions', 'serving']
        for field in required_fields:
            if not form_data.get(field) or not form_data[field].strip():
                errors[field] = f"The {field.replace('_', ' ')} field is required."

        if not uploaded_file or uploaded_file.filename == '':
            errors['image'] = 'An image file is required.'
        elif not allowed_file(uploaded_file.filename):
            errors['image'] = 'Invalid file type. Please upload an image (png, jpg, jpeg, gif).'

        if errors:
            session['errors'] = errors
            session['form_data'] = form_data
            session['form_data']['ingredients'] = form_data.get('ingredients', '')
            session['form_data']['instructions'] = form_data.get('instructions', '')

            return redirect(url_for('recipes_page'))
        else:
            filename = secure_filename(uploaded_file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            try:
                uploaded_file.save(filepath)
                print(f"File saved successfully to {filepath}")

                new_recipe = {
                    'name': form_data['name'].strip(),
                    'image': f'uploads/{filename}',
                    'ingredients': [ing.strip() for ing in form_data['ingredients'].splitlines() if ing.strip()],
                    'instructions': form_data['instructions'].strip(),
                    'serving': form_data['serving'].strip()
                }

                recipes.append(new_recipe)
                print("New recipe added:", new_recipe)

                session.pop('errors', None)
                session.pop('form_data', None)

                return redirect(url_for('recipes_page'))

            except Exception as e:
                errors['general'] = 'An error occurred while saving the recipe.'
                print(f"Error saving file or processing recipe: {e}")
                session['errors'] = errors
                session['form_data'] = form_data
                return redirect(url_for('recipes_page'))

    errors = session.pop('errors', {})
    form_data = session.pop('form_data', {})

    return render_template('recipes.html', recipes=recipes, errors=errors, form_data=form_data)


@app.route('/delete_recipe', methods=['GET', 'POST'])
def delete_recipe_page():
    global recipes
    session.setdefault('delete_errors', [])

    if request.method == 'POST':
        delete_errors = []

        recipes_to_delete_indices = request.form.getlist('recipes_to_delete')

        if not recipes_to_delete_indices:
             delete_errors.append("Please select at least one recipe to delete.")

        indices_to_delete = []
        for index_str in recipes_to_delete_indices:
            try:
                index = int(index_str)
                if 0 <= index < len(recipes):
                    indices_to_delete.append(index)
                else:
                    delete_errors.append(f"Invalid index received: {index_str}. Recipe not found.")
            except ValueError:
                delete_errors.append(f"Invalid data received for deletion.")

        if delete_errors:
            session['delete_errors'] = delete_errors
            return redirect(url_for('delete_recipe_page'))

        indices_to_delete.sort(reverse=True)

        for index in indices_to_delete:
            if 0 <= index < len(recipes):
                del recipes[index]
                print(f"Deleted recipe at index {index}")

        session.pop('delete_errors', None)

        return redirect(url_for('delete_recipe_page'))

    delete_errors = session.pop('delete_errors', [])

    return render_template('delete_recipe.html', recipes=recipes, delete_errors=delete_errors)


if __name__ == '__main__':
    app.run(debug=True)