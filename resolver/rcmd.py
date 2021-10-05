# -*- coding: utf-8 -*-

from sceptre.resolvers import Resolver
import os
import shlex
import subprocess


class SceptreResolverCmd(Resolver):
    NAME = 'rcmd'

    def __init__(self, *args, **kwargs):
        super(SceptreResolverCmd, self).__init__(*args, **kwargs)

    def resolve(self):
        '''
        Executes a command in an environment shell.
        :return: the resulting output from the executed command
        '''
        
        '''
            command: aws --profile {profile} example --p2 {param2} --p3 {param3}
            params: 
              profile: my-legacy-profile
              param2: !stack_output app/stack.yaml::VAR1_OUTPUT
              param3: anyvalue
            environment:
              AWS_PROFILE: my-profile
              VAR1: !stack_output app/stack.yaml::VAR1_OUTPUT
            
        '''
        profile = self.stack.profile or os.getenv('AWS_PROFILE')
        env = os.environ.copy()
        
        if isinstance(self.argument, dict):
            params = self.argument.get('params', {})
            environment = self.argument.get('environment', {})
            
            for opt in 'params', 'environment':
                for k, v in self.argument.get(opt, {}).items():
                    if isinstance(v, Resolver):
                        self.argument[opt][k] = v.resolve()
                        self.logger.debug('[%s] resolved "%s" to "%s"', 
                                          self.NAME, k, params[k])                
                                      
            env.update(environment)
            
            # backward compatibility
            profile = self.argument.get('profile', profile)
            
            # AWS_PROFILE in 'environment' options key should have precedence
            # over any default choice
            profile = environment.get('AWS_PROFILE', profile)
            cmd = self.argument['command'].format(**params)
        else:
            cmd = self.argument
            
        # backward compatibility
        env['AWS_PROFILE'] = profile
        
        args = shlex.split(cmd)
        p = subprocess.run(args, env=env, check=True, capture_output=True)
        
        return p.stdout.decode(os.getenv('SHELL_ENCODING', 'utf-8'))
