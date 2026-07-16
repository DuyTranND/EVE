from skfuzzy import control as ctrl
import pickle
from src.settings import settings

class Fuzzy():
    def __init__(self):
        self.goar_model = self.load_model(settings.paths.fuzzy_models / "obstacle_avoidance.pkl")
        self.foll_model = self.load_model(settings.paths.fuzzy_models / "person_following.pkl")
        
        
    def load_model(self, model_path):
        with open(model_path, 'rb') as file:
            control = pickle.load(file)
        simulation = ctrl.ControlSystemSimulation(control)

        return simulation

    def go_around(self, LL = 0.0, FF = 0.0, RR = 0.0):
        self.goar_model.input['L'] = LL
        self.goar_model.input['F'] = FF
        self.goar_model.input['R'] = RR
        
        self.goar_model.compute()
        v = self.goar_model.output['v']
        w = self.goar_model.output['w']
        
        return v, w
    
    def follow(self, EE = 0.0, WW = 0.0):
        self.foll_model.input['E'] = EE
        self.foll_model.input['W'] = WW
        
        self.foll_model.compute()
        v = self.foll_model.output['v']
        w = self.foll_model.output['w']
        
        return v, w
    
if __name__ == "__main__":
    fuzzy = Fuzzy()
    print("go around:", fuzzy.go_around(LL=1.5, FF=0.5, RR=1.5))
    print("follow:", fuzzy.follow(EE=-5.0, WW=150))
