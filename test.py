# import panda
# import plotly.graph_objs as go
# import plotly.express as px
# from dash import Dash, dcc, html, Input, Output
#
# app = Dash(__name__)
#
# # Initial position of the tool end
# initial_x, initial_y = 234.05, -10.92
#
# app.layout = html.Div([
#     dcc.Graph(id='interactive-graph', config={'editable': True}),
#     html.P(id='coordinates-output', children=f"Initial Coordinates: ({initial_x}, {initial_y})")
# ])
#
#
# @app.callback(
#     Output('interactive-graph', 'figure'),
#     Output('coordinates-output', 'children'),
#     Input('interactive-graph', 'relayoutData')
# )
# def update_figure(relayout_data):
#     if relayout_data and 'shapes[0].x0' in relayout_data:
#         new_x = relayout_data['shapes[0].x0']
#         new_y = relayout_data['shapes[0].y0']
#     else:
#         new_x, new_y = initial_x, initial_y
#
#     fig = go.Figure()
#
#     # Plot the tool end point
#     fig.add_trace(go.Scatter(x=[new_x], y=[new_y], mode='markers', marker=dict(color='red', size=10)))
#
#     # Add draggable shape
#     fig.update_layout(
#         shapes=[
#             dict(
#                 type="circle",
#                 x0=new_x - 5, y0=new_y - 5, x1=new_x + 5, y1=new_y + 5,
#                 xref="x", yref="y",
#                 line_color="red"
#             )
#         ]
#     )
#
#     fig.update_xaxes(range=[-400, 400])
#     fig.update_yaxes(range=[-300, 300])
#     fig.update_layout(title='Drag the red dot', dragmode='drawopenpath')
#
#     return fig, f"New Coordinates: ({new_x:.2f}, {new_y:.2f})"
#
#
# if __name__ == '__main__':
#     app.run_server(debug=True)

x_list = []
y_list = []

for i in x_list:
    for j in y_list:
        motionActuate(i,j)
        time.sleep(1)

