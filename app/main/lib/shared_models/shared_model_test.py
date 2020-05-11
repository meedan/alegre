from app.main.lib.shared_models.shared_model import SharedModel

class SharedModelTest(SharedModel):
  def load(self):
    pass

  def respond(self, analysis_value):
    return [0.0]

  def similarity(self, valueA, valueB):
    return 0.0
