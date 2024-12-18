import os
from google.cloud import firestore

class FirestoreDB:
    def __init__(self):
        # Ensure that GOOGLE_APPLICATION_CREDENTIALS is set to your service account JSON
        self.db = firestore.Client()

    def create_user(self, email, password_hash, subscription_tier):
        doc_ref = self.db.collection('users').document(email)
        doc_ref.set({
            'email': email,
            'password': password_hash,
            'subscription_tier': subscription_tier
        })

    def get_user_by_email(self, email):
        doc = self.db.collection('users').document(email).get()
        if doc.exists:
            return doc.to_dict()
        return None

    def create_research_project(self, user_email, prompt, pipeline_result):
        doc_ref = self.db.collection('research_projects').document()
        doc_ref.set({
            'user_email': user_email,
            'prompt': prompt,
            'pipeline_result': pipeline_result,
            'published_paper': None,
            'verification_report': None,
            'peer_review_report': None
        })
        return doc_ref.id

    def get_projects_for_user(self, user_email):
        docs = self.db.collection('research_projects').where('user_email', '==', user_email).stream()
        projects = []
        for d in docs:
            p = d.to_dict()
            p['id'] = d.id
            projects.append(p)
        return projects

    def update_project_field(self, project_id, field_name, value):
        doc_ref = self.db.collection('research_projects').document(project_id)
        doc_ref.update({field_name: value})

    def publish_paper(self, project_id):
        doc_ref = self.db.collection('research_projects').document(project_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            prompt = data.get('prompt', '')
            pipeline_result = data.get('pipeline_result', '')
            published_text = f"**Paper Title:** Automated Discovery from Prompt: '{prompt}'\n\n{pipeline_result}\n\n**Status:** Published to arXiv (Mock)"
            doc_ref.update({'published_paper': published_text})
            return True
        return False