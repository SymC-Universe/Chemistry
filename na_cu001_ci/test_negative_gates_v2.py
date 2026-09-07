#!/usr/bin/env python3
from __future__ import annotations
import argparse,contextlib,io,json,subprocess,tempfile,unittest
from pathlib import Path

import bulk_runner_v2 as bulk_runner
import validate_integration_chain_v2 as vic

HERE=Path(__file__).resolve().parent

class NegativeGateTests(unittest.TestCase):
    def write_summary(self,root,ecut,k,a0,e0):
        records=[]
        for a in bulk_runner.LATTICES:
            e=e0+2.0*(a-a0)**2
            records.append({'a_angstrom':a,'returncode':0,'job_done':True,'scf_converged':True,'final_energy_ev_per_atom':e})
        d={'schema':'na-cu001-bulk-matrix-v0.3','ecutwfc_ry':ecut,'ecutrho_ry':3*ecut,'kmesh':k,'records':records}
        p=root/f'summary_e{ecut}_k{k}.json';p.write_text(json.dumps(d));return p

    def test_bulk_selector_rejects_lattice_only_pass(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            for e in bulk_runner.REGISTERED_ECUTS:
                for k in bulk_runner.REGISTERED_KMESHES:
                    a0=3.64;e0=-99.98
                    if (e,k)==(50,8):a0=3.632;e0=-99.98
                    if (e,k)==(60,12):a0=3.631;e0=-99.9995
                    if e>60 or (e==60 and k>12):a0=3.6305;e0=-99.9997
                    self.write_summary(root,e,k,a0,e0)
            self.write_summary(root,80,16,3.63,-100.0)
            out=root/'result.json'
            bulk_runner.analyze(argparse.Namespace(summaries=str(root),out=str(out),reference_ecut=80,reference_kmesh=16))
            d=json.loads(out.read_text())
            by={(x['ecutwfc_ry'],x['kmesh']):x for x in d['candidates']}
            self.assertTrue(by[(50,8)]['joint_gate']['delta_a_pass'])
            self.assertFalse(by[(50,8)]['joint_gate']['delta_e_pass'])
            self.assertEqual((d['recommended_smallest']['ecutwfc_ry'],d['recommended_smallest']['kmesh']),(60,12))

    def test_validator_refuses_missing_and_nonpass_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);raw=root/'raw';raw.mkdir();plan=root/'plan.json'
            plan.write_text(json.dumps({'schema':'na-cu001-integration-closure-v0.2','stages':[{'id':1,'name':'x','artifact':'X.json','schema':'x-v1','dependencies':[]},{'id':2,'name':'integration','artifact':'I.json','schema':'i-v1','dependencies':[1],'generated_by_validator':True}]}))
            (root/'RAW_ARTIFACT_INDEX.json').write_text(json.dumps({'schema':'na-cu001-computational-manifest-v0.2','status':'PASS','files':[]}))
            result=vic.validate(plan,root,raw)
            self.assertEqual(result['status'],'HOLD')
            (root/'X.json').write_text(json.dumps({'schema':'x-v1','status':'HOLD'}))
            result=vic.validate(plan,root,raw)
            self.assertEqual(result['status'],'HOLD')

    def test_tier_linter_rejects_overbroad_label(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'bad.json';p.write_text(json.dumps({'verification_tier':'COMPUTATIONAL_FULL'}))
            proc=subprocess.run(['python',str(HERE/'tier_linter_v2.py'),str(p)],capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertIn('forbidden label',proc.stdout)

    def test_validation_cohort_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);c=root/'c.json';out1=root/'o1.json';out2=root/'o2.json'
            c.write_text(json.dumps([{'candidate_id':f's{i}'} for i in range(10)]))
            cmd=['python',str(HERE/'select_validation_cohort_v2.py'),'--candidates',str(c),'--protocol',str(HERE/'validation_selection_protocol_v0.1.json'),'--seed','1234','--n','3']
            subprocess.run(cmd+['--out',str(out1)],check=True,capture_output=True)
            subprocess.run(cmd+['--out',str(out2)],check=True,capture_output=True)
            self.assertEqual(json.loads(out1.read_text())['selected'],json.loads(out2.read_text())['selected'])

    def build_synthetic_full_chain(self, root: Path):
        raw=root/'raw';raw.mkdir()
        raw_file=raw/'qe.out';raw_file.write_text('synthetic raw output\n')
        raw_manifest={
            'schema':'na-cu001-computational-manifest-v0.2','status':'PASS',
            'files':[{'path':'qe.out','sha256':vic.sha256(raw_file),'size_bytes':raw_file.stat().st_size}]
        }
        (root/'RAW_ARTIFACT_INDEX.json').write_text(json.dumps(raw_manifest,indent=2)+'\n')
        for name in ('method_protocol_v0.2.json','validation_selection_protocol_v0.1.json',
                     'COMPUTATIONAL_PROCESS_AMENDMENT_v1.1.md','REPRODUCIBILITY_GUIDE_INSERT_v1.1.tex'):
            (root/name).write_text((HERE/name).read_text())
        (root/'COMPUTATIONAL_SOURCE_COMMIT.txt').write_text('synthetic-commit\n')
        (root/'SOURCE_CODE_MANIFEST.sha256').write_text('synthetic manifest\n')
        (root/'SOURCE_MANIFEST_VERIFICATION.txt').write_text('synthetic: OK\n')
        plan_path=HERE/'integration_closure_plan_v0.2.json'
        plan=json.loads(plan_path.read_text())
        written={}
        for stage in plan['stages']:
            if stage.get('generated_by_validator'):
                continue
            links=[]
            for dep in stage.get('dependencies',[]):
                dep_stage=next(x for x in plan['stages'] if int(x['id'])==int(dep))
                if dep_stage.get('generated_by_validator'):
                    continue
                dep_path=root/dep_stage['artifact']
                links.append({'path':dep_path.name,'sha256':vic.sha256(dep_path)})
            state_key='scientific_status' if int(stage['id'])==1 else 'status'
            state_value='bulk_convergence_passed_slab_not_yet_run' if int(stage['id'])==1 else 'PASS'
            payload={'schema':stage['schema'],state_key:state_value,'input_artifacts':links}
            path=root/stage['artifact'];path.write_text(json.dumps(payload,indent=2)+'\n');written[int(stage['id'])]=path
        return plan_path,raw,written

    def test_full_chain_validator_passes_then_rejects_raw_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,raw,_=self.build_synthetic_full_chain(root)
            result=vic.validate(plan,root,raw)
            self.assertEqual(result['status'],'PASS')
            self.assertEqual(result['required_nonresult_validation']['status'],'PASS')
            (raw/'qe.out').write_text('corrupted\n')
            result=vic.validate(plan,root,raw)
            self.assertEqual(result['status'],'HOLD')
            self.assertEqual(result['raw_artifact_validation']['status'],'HOLD')

    def test_full_chain_validator_rejects_missing_frozen_protocol(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,raw,_=self.build_synthetic_full_chain(root)
            (root/'method_protocol_v0.2.json').unlink()
            result=vic.validate(plan,root,raw)
            self.assertEqual(result['status'],'HOLD')
            self.assertEqual(result['required_nonresult_validation']['status'],'HOLD')

    def test_full_chain_validator_rejects_dependency_hash_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,raw,written=self.build_synthetic_full_chain(root)
            first=written[1]
            first.write_text(first.read_text()+' ')
            result=vic.validate(plan,root,raw)
            self.assertEqual(result['status'],'HOLD')
            self.assertTrue(any('hash mismatch' in e for stage in result['stages'] for e in stage['errors']))

    def test_validator_rejects_unlinked_declared_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);plan,raw,written=self.build_synthetic_full_chain(root)
            stage2=written[2];payload=json.loads(stage2.read_text());payload['input_artifacts']=[];stage2.write_text(json.dumps(payload))
            result=vic.validate(plan,root,raw)
            self.assertEqual(result['status'],'HOLD')
            self.assertTrue(any('dependency artifact not hash-linked' in e for e in result['stages'][1]['errors']))

    def test_na_probe_uses_authoritative_pointer_and_rejects_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);archive=root/'archive.tar.gz';archive.write_bytes(b'pinned archive')
            extracted=root/'extracted';meta=extracted/'mix-sssp-pbe-eff-lib-v2';meta.mkdir(parents=True)
            upf=extracted/'Na.test.upf';upf.write_text('<UPF><PP_HEADER element="Na"/></UPF>')
            (meta/'cutoffs.json').write_text(json.dumps({'Na':{'cutoff_wfc':50,'cutoff_rho':150}}))
            import hashlib
            digest=lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
            protocol=root/'protocol.json';out=root/'out.json'
            payload={'schema':'na-cu001-method-protocol-v0.2','status':'FROZEN_BEFORE_DOWNSTREAM_RESULTS','immutable_sources':{
                'sssp_pbe_efficiency_v2_archive_sha256':digest(archive),'na_upf_filename':upf.name,'na_upf_sha256':digest(upf),
                'na_authoritative_cutoff_metadata':{'relative_path':'mix-sssp-pbe-eff-lib-v2/cutoffs.json','json_pointer':'/Na','ecutwfc_ry':50.0,'ecutrho_ry':150.0}}}
            protocol.write_text(json.dumps(payload))
            cmd=['python',str(HERE/'na_pseudo_probe_v2.py'),'--archive-root',str(extracted),'--archive',str(archive),'--protocol',str(protocol),'--out',str(out)]
            subprocess.run(cmd,check=True,capture_output=True,text=True)
            self.assertEqual(json.loads(out.read_text())['authoritative_cutoffs']['recommended_ecutrho_ry'],150.0)
            (meta/'cutoffs.json').write_text(json.dumps({'Na':{'cutoff_wfc':60,'cutoff_rho':180}}))
            proc=subprocess.run(cmd,capture_output=True,text=True)
            self.assertNotEqual(proc.returncode,0)
            self.assertEqual(json.loads(out.read_text())['status'],'HOLD')

if __name__=='__main__':unittest.main(verbosity=2)
