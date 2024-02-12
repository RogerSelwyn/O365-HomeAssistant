---
title: To-Do Lists
nav_order: 9
---

# To-Do Lists

One To-Do List entity is created for each to-do list on the user account. Each sensor shows the number of incomplete to-do items as the status of the sensor. The `all_todos` attribute is an array of incomplete to-dos. The `overdue_todos` attribute shows any to-dos which have a due date and are overdue as an array.

### Display
In order to show the to-dos in the front end either use the HA inbuilt To-Do panel or a markdown card can be used. The following is an example that allows you to display a bulleted list subject from the `all_todos` array of todos.

```yaml
type: markdown
title: Todos
content: |-
  {% raw %}{% for todo in state_attr('todo.todos_sc_personal', 'all_todos') -%}
  - {{ todo['subject'] }}
  {% endfor %}{% endraw %}
```
