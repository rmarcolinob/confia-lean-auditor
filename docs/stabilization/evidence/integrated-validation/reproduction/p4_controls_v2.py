from run import run, PYTHON, ROOT, ENV
ENV['PYTHONPATH'] += ':'+str(ROOT/'artifacts/integrated-validation')
target='tests/test_tme_accepted_integration.py::test_five_problems_accepted_engine_persistence_api[full-4]'
for version in ('original','combined'):
    for seed in range(1,6):
        run('p4-pause-v2-%s-%d'%(version,seed),[PYTHON,'-m','pytest','-q','-p','p4_pause_v2',target],
            {'CONFIA_P4_CONTROL':version,'PYTHONHASHSEED':str(seed)})
