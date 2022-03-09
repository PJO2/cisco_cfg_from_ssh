# should yuse python v2.7 or 3.x
import tipyte

render_inbox = tipyte.template_to_function("tmpl.j0")
data = {'title': "Inbox", 'email': 'j.doe@example.com' } 
print (data)
print (render_inbox(data=data))

