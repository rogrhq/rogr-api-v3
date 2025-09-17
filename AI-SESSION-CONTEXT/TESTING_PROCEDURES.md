# Testing Procedures & Backend Information

**Purpose**: Persistent testing information to prevent session continuity gaps
**Date**: 2025-09-16
**Status**: Phase 2 Testing Procedures

---

## **Current Backend Information**

### **Remote Backend URLs**
- **Current Backend URL**: https://69780239-96f5-4ce3-b826-d3453286c75d-00-2q5k9aqq28xtu.picard.repl.co
- **Legacy URL (from old prompts)**: https://811efd66-721a-418d-978d-2fb9a8b674e6-00-18dh30ad08soc.janeway.replit.dev
- **Health Check**: `GET /health`
- **Main Testing Endpoint**: `POST /analyses`

### **Environment Configuration**
```bash
# .replit file settings for testing
USE_PARALLEL_EVIDENCE = "true"   # For parallel system testing
USE_EEG_PHASE_1 = "true"        # EEG methodology search
USE_EVIDENCE_SHEPHERD = "true"   # Evidence Shepherd integration
```

---

## **Phase 2 Testing Protocol**

### **L2.3 Integration Point Verification Tests**

#### **Test 1: ThreadSafeEvidenceWorker + WorkerResourceBundle**
```bash
curl -X POST "BACKEND_URL/analyses" \
-H "Content-Type: application/json" \
-d '{
  "input": "COVID-19 vaccines are safe and effective for preventing severe illness"
}' \
--max-time 60
```

#### **Test 2: ParallelEvidenceOrchestrator + EEG + ACI Integration**
```bash
curl -X POST "BACKEND_URL/analyses" \
-H "Content-Type: application/json" \
-d '{
  "input": "Climate change policies will destroy the economy"
}' \
--max-time 60
```

#### **Test 3: Performance Validation (<30s target)**
```bash
curl -X POST "BACKEND_URL/analyses" \
-H "Content-Type: application/json" \
-d '{
  "input": "Social media algorithms promote political polarization"
}' \
--max-time 35
```

### **Expected Success Criteria**
- **Response Time**: <30s total processing
- **Status Code**: 200 OK
- **Response Format**: Valid TrustCapsule JSON
- **Evidence Count**: 5+ pieces of processed evidence
- **Consensus Score**: Valid numerical score (0-100)

### **Failure Scenarios & Debugging**
- **500 Error**: Check TEST.LOGS.txt for import errors
- **Timeout**: Parallel system not performing, likely falling back to legacy
- **Empty Response**: ClaimMiner integration issue

---

## **Test Claims Library**

### **ACI Pipeline Validation Claims**
```json
{
  "medical": "COVID-19 vaccines are safe and effective for preventing severe illness",
  "economic": "Minimum wage increases reduce unemployment rates in small businesses",
  "scientific": "Climate change is primarily caused by human activities and fossil fuel emissions",
  "semantic_test": "Climate change policies will destroy the economy",
  "logical_test": "Smoking causes cancer",
  "domain_test": "Remote work is more productive than office work"
}
```

### **Performance Baseline Reference**
- **Legacy System**: 396s average processing time
- **Target**: <30s (87% improvement)
- **Individual Claim Target**: <15s (70% improvement)

---

## **Session Handoff Protocol**

### **Before Each Session**
1. **Update Backend URL**: Ensure current deployed URL is documented
2. **Verify Environment**: Check USE_PARALLEL_EVIDENCE=true is set
3. **Test Health Check**: `curl BACKEND_URL/health` should return `{"ok": true}`

### **During Testing**
1. **Document Results**: Update this file with test outcomes
2. **Log Performance**: Record actual processing times vs targets
3. **Track Issues**: Note any errors or fallback scenarios

### **Session End**
1. **Update Status**: Record which tests passed/failed
2. **Next Session Prep**: Clear objectives based on testing results
3. **Backend Status**: Note if backend changes needed for next session

---

## **Integration with Existing Files**

### **SESSION_START_PROTOCOL.md Integration**
- **Step 2**: Add "Check TESTING_PROCEDURES.md for current backend URL"
- **Step 4**: Add "Confirm testing environment ready per TESTING_PROCEDURES.md"

### **CURRENT_SESSION_STATE.md Updates**
- Include testing status and backend validation results
- Reference specific tests completed/pending

---

## **Version History**
- **2025-09-16**: Initial creation - Phase 2 testing procedures established
- **[Future]**: Backend URL updates, additional test scenarios, performance benchmarks

---

**This file should be updated by each AI session with current backend information and testing results to ensure continuity.**