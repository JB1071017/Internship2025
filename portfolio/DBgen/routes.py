from flask import Blueprint, render_template, request

dbgen_bp = Blueprint(
    'dbgen',
    __name__,
    url_prefix='/dbgen',
    template_folder='templates',
    static_folder='static'
)

# Route to render the DB Generator form
@dbgen_bp.route('/')
def index():
    return render_template('dbgen_index.html')

# Route to handle the form submission
@dbgen_bp.route('/generate', methods=['POST', 'GET'])
def generate():
    if request.method == 'POST':
        topic = request.form.get('topic')
        n_columns = int(request.form.get('n_columns', 5))
        n_rows = int(request.form.get('n_rows', 100))
        column_names = request.form.get('column_names', '')
        include_custom = 'include_custom' in request.form

    # You can generate your CSV or data logic here

    return render_template(
        'dbgen_result.html',
        topic=topic,
        n_columns=n_columns,
        n_rows=n_rows,
        column_names=column_names,
        include_custom=include_custom
    )
